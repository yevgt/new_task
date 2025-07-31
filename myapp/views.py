from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from .models import Task, SubTask, Category
from .serializers import (
    TaskCreateSerializer,
    TaskListSerializer,
    TaskDetailSerializer,
    CategorySerializer
)

def hello_view(request):
    return HttpResponse("<h1>Hello, YevgeniyG</h1>")


def tasks_view(request):
    tasks = Task.objects.all().prefetch_related('categories', 'subtasks')
    categories = Category.objects.all()

    context = {
        'tasks': tasks,
        'categories': categories,
    }
    return render(request, 'myapp/tasks.html', context)


# REST API представления

class TaskCreateAPIView(generics.CreateAPIView):
    """
    Эндпоинт для создания новой задачи.

    POST /api/tasks/create/
    """
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save()
            # Возвращаем детальную информацию о созданной задаче
            detail_serializer = TaskDetailSerializer(task)
            return Response(
                {
                    'message': 'Задача успешно создана',
                    'task': detail_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskListAPIView(generics.ListAPIView):
    """
    Эндпоинт для получения списка всех задач.

    GET /api/tasks/

    Поддерживает фильтрацию по:
    - status: фильтр по статусу (new, in_progress, pending, blocked, done)
    - is_overdue: фильтр просроченных задач (true/false)
    - categories: фильтр по категориям (ID категории)

    Поддерживает поиск по:
    - title: поиск по названию
    - description: поиск по описанию

    Поддерживает сортировку по:
    - created_at: дата создания
    - deadline: дедлайн
    - title: название
    """
    queryset = Task.objects.all().prefetch_related('categories', 'subtasks')
    serializer_class = TaskListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация по статусу
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Фильтрация просроченных задач
        is_overdue = self.request.query_params.get('is_overdue')
        if is_overdue == 'true':
            queryset = queryset.filter(
                deadline__lt=timezone.now()
            ).exclude(status='done')
        elif is_overdue == 'false':
            queryset = queryset.filter(
                Q(deadline__gte=timezone.now()) | Q(status='done')
            )

        # Фильтрация по категориям
        category_id = self.request.query_params.get('categories')
        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        # Поиск
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Сортировка
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)

        return queryset.distinct()


class TaskDetailAPIView(generics.RetrieveAPIView):
    """
    Эндпоинт для получения конкретной задачи по ID.

    GET /api/tasks/{id}/
    """
    queryset = Task.objects.all().prefetch_related('categories', 'subtasks')
    serializer_class = TaskDetailSerializer
    lookup_field = 'id'


@api_view(['GET'])
def task_statistics_view(request):
    """
    Агрегирующий эндпоинт для получения статистики задач.

    GET /api/tasks/statistics/

    Возвращает:
    - Общее количество задач
    - Количество задач по каждому статусу
    - Количество просроченных задач
    - Количество задач по категориям
    - Статистику по подзадачам
    """

    # Общее количество задач
    total_tasks = Task.objects.count()

    # Количество задач по статусам
    status_stats = Task.objects.values('status').annotate(count=Count('id'))
    status_counts = {item['status']: item['count'] for item in status_stats}

    # Все возможные статусы с нулевыми значениями по умолчанию
    all_statuses = ['new', 'in_progress', 'pending', 'blocked', 'done']
    status_breakdown = {status: status_counts.get(status, 0) for status in all_statuses}

    # Просроченные задачи
    overdue_tasks = Task.objects.filter(
        deadline__lt=timezone.now()
    ).exclude(status='done').count()

    # Статистика по категориям
    category_stats = Category.objects.annotate(
        task_count=Count('tasks')
    ).values('name', 'task_count')

    # Статистика по подзадачам
    total_subtasks = SubTask.objects.count()
    subtask_status_stats = SubTask.objects.values('status').annotate(count=Count('id'))
    subtask_status_counts = {item['status']: item['count'] for item in subtask_status_stats}
    subtask_breakdown = {status: subtask_status_counts.get(status, 0) for status in all_statuses}

    # Задачи без подзадач
    tasks_without_subtasks = Task.objects.filter(subtasks__isnull=True).count()

    # Средний процент выполнения задач (подзадачи в статусе done)
    tasks_with_subtasks = Task.objects.filter(subtasks__isnull=False).distinct()
    completion_rates = []
    for task in tasks_with_subtasks:
        total_subs = task.subtasks.count()
        completed_subs = task.subtasks.filter(status='done').count()
        if total_subs > 0:
            completion_rates.append((completed_subs / total_subs) * 100)

    avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0

    # Формирование ответа
    statistics = {
        'overview': {
            'total_tasks': total_tasks,
            'total_subtasks': total_subtasks,
            'overdue_tasks': overdue_tasks,
            'tasks_without_subtasks': tasks_without_subtasks,
            'average_completion_rate': round(avg_completion_rate, 2)
        },
        'task_status_breakdown': status_breakdown,
        'subtask_status_breakdown': subtask_breakdown,
        'category_statistics': list(category_stats),
        'completion_metrics': {
            'completed_tasks': status_counts.get('done', 0),
            'in_progress_tasks': status_counts.get('in_progress', 0),
            'pending_tasks': status_counts.get('pending', 0),
            'blocked_tasks': status_counts.get('blocked', 0),
            'new_tasks': status_counts.get('new', 0)
        }
    }

    return Response(statistics)


# Дополнительный эндпоинт для получения списка категорий
class CategoryListAPIView(generics.ListAPIView):
    """
    Эндпоинт для получения списка всех категорий.

    GET /api/categories/
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer