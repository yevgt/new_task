from django.contrib import admin
from django.utils.html import format_html
from .models import Task, SubTask, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 25


class SubTaskInline(admin.TabularInline):
    """Inline для отображения подзадач в задаче."""
    model = SubTask
    extra = 2  # Количество пустых форм для создания новых подзадач
    fields = ['title', 'description', 'status', 'deadline']
    readonly_fields = ['created_at']

    # Дополнительные настройки для удобства
    classes = ['collapse']  # Сворачиваемая секция
    verbose_name = "Подзадача"
    verbose_name_plural = "Подзадачи"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Административная панель для модели Task."""
    list_display = ['title', 'status', 'deadline', 'created_at', 'is_overdue', 'categories_list']
    list_filter = ['status', 'categories', 'created_at', 'deadline']
    search_fields = ['title', 'description']
    filter_horizontal = ['categories']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    inlines = [SubTaskInline] # Инлайн формы для подзадач
    list_per_page = 25

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'categories'),
            'classes': ('wide',)
        }),
        ('Статус и сроки', {
            'fields': ('status', 'deadline'),
            'classes': ('wide',)
        }),
        ('Информация о создании', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at']

    def short_title(self, obj):
        """Отображение укороченного названия задачи в списке."""
        if len(obj.title) > 10:
            return f"{obj.title[:10]}..."
        return obj.title

    short_title.short_description = 'Название'
    short_title.admin_order_field = 'title'  # Позволяет сортировать по этому полю

    def is_overdue(self, obj):
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">Да</span>'
            )
        return format_html(
            '<span style="color: green;">Нет</span>'
        )
    is_overdue.boolean = False  # Отключаем стандартную булеву иконку
    is_overdue.short_description = 'Просрочена'

    def categories_list(self, obj):
        """Отображение списка категорий в списке задач."""
        categories = obj.categories.all()
        if categories:
            category_names = [cat.name for cat in categories]
            return ", ".join(category_names)
        return "Без категории"

    categories_list.short_description = 'Категории'


# Кастомный action для изменения статуса подзадач на "Done"
def mark_as_done(modeladmin, request, queryset):
    """Action для пометки выбранных подзадач как выполненных."""
    updated_count = queryset.update(status='done')
    if updated_count == 1:
        message = "1 подзадача была помечена как выполненная."
    else:
        message = f"{updated_count} подзадач были помечены как выполненные."

    modeladmin.message_user(request, message)


# Настройка отображения action
mark_as_done.short_description = "Пометить выбранные подзадачи как выполненные"

@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    """Административная панель для модели SubTask."""
    list_display = ['title', 'task', 'status', 'deadline', 'created_at', 'is_overdue']
    list_filter = ['status', 'task', 'created_at', 'deadline']
    search_fields = ['title', 'description', 'task__title']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25
    actions = [mark_as_done]  # Добавляем кастомный action

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'task'),
            'classes': ('wide',)
        }),
        ('Статус и сроки', {
            'fields': ('status', 'deadline'),
            'classes': ('wide',)
        }),
        ('Информация о создании', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at']

    def short_title(self, obj):
        """Отображение укороченного названия подзадачи в списке."""
        if len(obj.title) > 10:
            return f"{obj.title[:10]}..."
        return obj.title

    short_title.short_description = 'Название'
    short_title.admin_order_field = 'title'

    def task_full_name(self, obj):
        """Отображение полного названия основной задачи."""
        return obj.task.title

    task_full_name.short_description = 'Основная задача'
    task_full_name.admin_order_field = 'task__title'

    def is_overdue(self, obj):
        """Отображение статуса просрочки в списке."""
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">Да</span>'
            )
        return format_html(
            '<span style="color: green;">Нет</span>'
        )

    is_overdue.boolean = False
    is_overdue.short_description = 'Просрочена'

    # Автозаполнение поля task с отображением полного названия
    autocomplete_fields = ['task']


# # Дополнительные настройки админки
# admin.site.site_header = "Task Manager Administration"
# admin.site.site_title = "Task Manager Admin"
# admin.site.index_title = "Добро пожаловать в панель управления Task Manager"

# Кастомизация TaskAdmin для автозаполнения
# Добавляем поиск для автозаполнения в Task
TaskAdmin.search_fields = ['title', 'description']

# Дополнительные настройки админки
admin.site.site_header = "Task Manager Administration"
admin.site.site_title = "Task Manager Admin"
admin.site.index_title = "Добро пожаловать в панель управления Task Manager"


# Дополнительная настройка для улучшения UX
class TaskAutocompleteAdmin(admin.ModelAdmin):
    """Дополнительный класс для автозаполнения задач."""
    search_fields = ['title']

    def get_search_results(self, request, queryset, search_term):
        """Кастомный поиск для автозаполнения с полным названием."""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


# Переопределяем регистрацию Task для поддержки автозаполнения
admin.site.unregister(Task)
admin.site.register(Task, TaskAdmin)