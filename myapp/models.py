from django.db import models
from django.utils import timezone

class CategoryManager(models.Manager):
    """
    Кастомный менеджер для модели Category с поддержкой мягкого удаления
    """
    def get_queryset(self):
        """Переопределяем get_queryset для исключения удаленных записей по умолчанию"""
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """Метод для получения всех записей, включая удаленные"""
        return super().get_queryset()

    def deleted_only(self):
        """Метод для получения только удаленных записей"""
        return super().get_queryset().filter(is_deleted=True)

class Category(models.Model):
    """Категория выполнения."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание")  # Добавьте это поле
    color = models.CharField(max_length=7, blank=True, verbose_name="Цвет", help_text="Цвет в формате HEX")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    # Поля для мягкого удаления
    is_deleted = models.BooleanField(default=False, verbose_name="Удалено")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата удаления")

    # Используем кастомный менеджер
    objects = CategoryManager()

    class Meta:
        db_table = 'task_manager_category'
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        unique_together = [['name']]

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        """Переопределяем метод удаления для мягкого удаления"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self):
        """Метод для полного удаления записи из базы данных"""
        super().delete()

    def restore(self):
        """Метод для восстановления удаленной записи"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class Task(models.Model):
    """Задача для выполнения."""

    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In progress'),
        ('pending', 'Pending'),
        ('blocked', 'Blocked'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название задачи")
    description = models.TextField(blank=True, verbose_name="Описание задачи")
    categories = models.ManyToManyField(
        Category,
        blank=True,
        verbose_name="Категории задачи",
        related_name="tasks"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус задачи"
    )
    deadline = models.DateTimeField(verbose_name="Дедлайн")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-created_at']
        # Уникальность названия для одной даты (используем unique_together)
        unique_together = [['title', 'deadline']]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_overdue(self):
        """Проверка просрочена ли задача."""
        return self.deadline < timezone.now() and self.status != 'done'

    def get_short_title(self):
        """Возвращает укороченное название для отображения."""
        if len(self.title) > 10:
            return f"{self.title[:10]}..."
        return self.title

    def get_absolute_url(self):
        """URL для просмотра задачи."""
        from django.urls import reverse
        return reverse('admin:myapp_task_change', args=[self.pk])

    @property
    def subtasks_count(self):
        """Количество подзадач."""
        return self.subtasks.count()

    @property
    def completed_subtasks_count(self):
        """Количество выполненных подзадач."""
        return self.subtasks.filter(status='done').count()

class SubTask(models.Model):
    """Отдельная часть основной задачи (Task)."""

    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In progress'),
        ('pending', 'Pending'),
        ('blocked', 'Blocked'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название подзадачи")
    description = models.TextField(blank=True, verbose_name="Описание подзадачи")
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='subtasks',
        verbose_name="Основная задача"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус подзадачи"
    )
    deadline = models.DateTimeField(verbose_name="Дедлайн")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        db_table = 'task_manager_subtask'
        verbose_name = "SubTask"
        verbose_name_plural = "SubTasks"
        ordering = ['-created_at']
        unique_together = [['title']]

    def __str__(self):
        return f"{self.task.title} -> {self.title} ({self.get_status_display()})"

    @property
    def is_overdue(self):
        """Проверка просрочена ли подзадача."""
        return self.deadline < timezone.now() and self.status != 'done'

    def get_short_title(self):
        """Возвращает укороченное название для отображения."""
        if len(self.title) > 10:
            return f"{self.title[:10]}..."
        return self.title