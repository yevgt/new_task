from rest_framework import serializers
from .models import Task, SubTask, Category
from django.utils import timezone


class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения категорий.
    Используется для list, retrieve и ответов после create/update.
    """
    tasks_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'description',
            'color',
            'created_at',
            'updated_at',
            'tasks_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tasks_count']

    def get_tasks_count(self, obj):
        """Подсчет количества задач в категории"""
        return obj.tasks.count() if hasattr(obj, 'tasks') else 0

# Задание 2: CategoryCreateSerializer с переопределенными методами create и update
class CategoryCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления категорий с проверкой уникальности."""

    class Meta:
        model = Category
        fields = ['name', 'description', 'color']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True},
            'color': {'required': False, 'allow_blank': True},
        }

    def validate_name(self, value):
        """Валидация названия категории"""
        if not value or not value.strip():
            raise serializers.ValidationError("Название категории не может быть пустым.")

        if len(value.strip()) < 2:
            raise serializers.ValidationError("Название категории должно содержать минимум 2 символа.")

        if len(value.strip()) > 100:
            raise serializers.ValidationError("Название категории не может превышать 100 символов.")

        return value.strip()

    def validate_color(self, value):
        """Валидация цвета в формате HEX"""
        if value and value.strip():
            value = value.strip()
            if not value.startswith('#'):
                value = '#' + value

            if len(value) != 7:
                raise serializers.ValidationError("Цвет должен быть в формате HEX (#RRGGBB).")

            try:
                int(value[1:], 16)  # Проверяем, что это валидный HEX
            except ValueError:
                raise serializers.ValidationError("Цвет должен содержать только валидные HEX символы.")

            return value
        return value

    def create(self, validated_data):
        """Переопределенный метод create с проверкой уникальности названия."""
        name = validated_data.get('name')

        # Проверяем уникальность названия (регистронезависимо)
        if Category.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError({
                'name': 'Категория с таким названием уже существует.'
            })

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Переопределенный метод update с проверкой уникальности названия."""
        name = validated_data.get('name', instance.name)

        # Проверяем уникальность названия, исключая текущую категорию
        if Category.objects.filter(name__iexact=name).exclude(id=instance.id).exists():
            raise serializers.ValidationError({
                'name': 'Категория с таким названием уже существует.'
            })

        return super().update(instance, validated_data)

    def validate_name(self, value):
        """Дополнительная валидация названия категории."""
        if not value or not value.strip():
            raise serializers.ValidationError("Название категории не может быть пустым.")

        if len(value.strip()) < 2:
            raise serializers.ValidationError("Название категории должно содержать минимум 2 символа.")

        return value.strip()

    def to_representation(self, instance):
        """
        Возвращаем полное представление объекта после создания/обновления
        """
        return CategorySerializer(instance, context=self.context).data


# Задание 1: SubTaskCreateSerializer с переопределением поля created_at
class SubTaskCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подзадач с read_only полем created_at."""

    # Переопределяем поле created_at как read_only
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = SubTask
        fields = ['id', 'title', 'description', 'task', 'status', 'deadline', 'created_at']
        read_only_fields = ['created_at']  # Альтернативный способ указания read_only полей

    def validate_deadline(self, value):
        """Проверка, что дедлайн не в прошлом."""
        if value < timezone.now():
            raise serializers.ValidationError("Дедлайн подзадачи не может быть в прошлом.")
        return value

    def validate_title(self, value):
        """Валидация названия подзадачи."""
        if not value or not value.strip():
            raise serializers.ValidationError("Название подзадачи не может быть пустым.")
        return value.strip()


class SubTaskSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для модели SubTask."""
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = SubTask
        fields = ['id', 'title', 'description', 'status', 'deadline', 'created_at', 'is_overdue']
        read_only_fields = ['created_at']


class SubTaskUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления подзадач."""

    class Meta:
        model = SubTask
        fields = ['title', 'description', 'status', 'deadline']

    def validate_deadline(self, value):
        """Проверка, что дедлайн не в прошлом."""
        if value < timezone.now():
            raise serializers.ValidationError("Дедлайн подзадачи не может быть в прошлом.")
        return value


# Задание 4: TaskCreateSerializer с валидацией deadline
class TaskCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания задачи с валидацией deadline."""
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'deadline', 'categories']

    def validate_deadline(self, value):
        """Переопределенный метод для проверки, что дедлайн не в прошлом."""
        if value < timezone.now():
            raise serializers.ValidationError("Дедлайн задачи не может быть в прошлом.")
        return value

    def validate_title(self, value):
        """Проверка уникальности названия задачи."""
        if not value or not value.strip():
            raise serializers.ValidationError("Название задачи не может быть пустым.")

        if Task.objects.filter(title__iexact=value.strip()).exists():
            raise serializers.ValidationError("Задача с таким названием уже существует.")
        return value.strip()

    def validate(self, data):
        """Общая валидация всех полей."""
        # Дополнительная проверка: если статус 'done', дедлайн может быть в прошлом
        if data.get('status') == 'done':
            # Для завершенных задач не проверяем дедлайн
            pass
        elif data.get('deadline') and data.get('deadline') < timezone.now():
            raise serializers.ValidationError({
                'deadline': 'Дедлайн не может быть в прошлом для незавершенных задач.'
            })

        return data


class TaskListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка задач."""
    categories = CategorySerializer(many=True, read_only=True)
    subtasks_count = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'deadline',
            'created_at', 'categories', 'subtasks_count', 'is_overdue'
        ]

    def get_subtasks_count(self, obj):
        """Возвращает количество подзадач."""
        return obj.subtasks.count()


# Задание 3: TaskDetailSerializer с вложенными сериализаторами
class TaskDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о задаче с вложенными подзадачами."""
    categories = CategorySerializer(many=True, read_only=True)
    # Используем вложенный сериализатор для подзадач
    subtasks = SubTaskSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    subtasks_count = serializers.SerializerMethodField()
    completed_subtasks_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'deadline', 'created_at',
            'categories', 'subtasks', 'is_overdue', 'subtasks_count',
            'completed_subtasks_count', 'progress_percentage'
        ]

    def get_subtasks_count(self, obj):
        """Возвращает общее количество подзадач."""
        return obj.subtasks.count()

    def get_completed_subtasks_count(self, obj):
        """Возвращает количество выполненных подзадач."""
        return obj.subtasks.filter(status='done').count()

    def get_progress_percentage(self, obj):
        """Возвращает процент выполнения задачи на основе подзадач."""
        total_subtasks = obj.subtasks.count()
        if total_subtasks == 0:
            return 0

        completed_subtasks = obj.subtasks.filter(status='done').count()
        return round((completed_subtasks / total_subtasks) * 100, 2)


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления задач."""
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'deadline', 'categories']

    def validate_deadline(self, value):
        """Проверка дедлайна при обновлении."""
        # Если задача завершена, дедлайн может быть любым
        if self.instance and self.instance.status == 'done':
            return value

        if value < timezone.now():
            raise serializers.ValidationError("Дедлайн не может быть в прошлом.")
        return value

    def validate_title(self, value):
        """Проверка уникальности названия при обновлении."""
        if not value or not value.strip():
            raise serializers.ValidationError("Название задачи не может быть пустым.")

        # Исключаем текущую задачу из проверки уникальности
        if (self.instance and
                Task.objects.filter(title__iexact=value.strip()).exclude(id=self.instance.id).exists()):
            raise serializers.ValidationError("Задача с таким названием уже существует.")

        return value.strip()