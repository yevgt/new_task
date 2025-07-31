from rest_framework import serializers
from .models import Task, SubTask, Category
from django.utils import timezone


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для модели Category."""

    class Meta:
        model = Category
        fields = ['id', 'name']


class SubTaskSerializer(serializers.ModelSerializer):
    """Сериализатор для модели SubTask."""

    class Meta:
        model = SubTask
        fields = ['id', 'title', 'description', 'status', 'deadline', 'created_at']
        read_only_fields = ['created_at']


class TaskCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания задачи."""
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'deadline', 'categories']

    def validate_deadline(self, value):
        """Проверка, что дедлайн не в прошлом."""
        if value < timezone.now():
            raise serializers.ValidationError("Дедлайн не может быть в прошлом.")
        return value

    def validate_title(self, value):
        """Проверка уникальности названия."""
        if Task.objects.filter(title=value).exists():
            raise serializers.ValidationError("Задача с таким названием уже существует.")
        return value


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


class TaskDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о задаче."""
    categories = CategorySerializer(many=True, read_only=True)
    subtasks = SubTaskSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    subtasks_count = serializers.SerializerMethodField()
    completed_subtasks_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'deadline', 'created_at',
            'categories', 'subtasks', 'is_overdue', 'subtasks_count',
            'completed_subtasks_count'
        ]

    def get_subtasks_count(self, obj):
        """Возвращает общее количество подзадач."""
        return obj.subtasks.count()

    def get_completed_subtasks_count(self, obj):
        """Возвращает количество выполненных подзадач."""
        return obj.subtasks.filter(status='done').count()