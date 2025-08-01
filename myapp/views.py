from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Task, SubTask, Category
from .serializers import (
    TaskCreateSerializer,
    TaskListSerializer,
    TaskDetailSerializer,
    TaskUpdateSerializer,
    CategorySerializer,
    CategoryCreateSerializer,
    SubTaskCreateSerializer,
    SubTaskSerializer,
    SubTaskUpdateSerializer
)


# Существующие представления для веб-интерфейса
def hello_view(request):
    return HttpResponse("<h1>Hello, YourName</h1>")


def tasks_view(request):
    tasks = Task.objects.all().prefetch_related('categories', 'subtasks')
    categories = Category.objects.all()

    context = {
        'tasks': tasks,
        'categories': categories,
    }
    return render(request, 'myapp/tasks.html', context)


# REST API представления для задач

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


class TaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Эндпоинт для получения, обновления и удаления конкретной задачи по ID.

    GET /api/tasks/{id}/
    PUT /api/tasks/{id}/
    PATCH /api/tasks/{id}/
    DELETE /api/tasks/{id}/
    """
    queryset = Task.objects.all().prefetch_related('categories', 'subtasks')
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TaskUpdateSerializer
        return TaskDetailSerializer


# Задание 5: Классы представлений для работы с подзадачами

class SubTaskListCreateView(APIView):
    """
    Представление для создания и получения списка подзадач.

    GET /api/subtasks/ - получить список всех подзадач
    POST /api/subtasks/ - создать новую подзадачу
    """

    def get(self, request):
        """Получение списка всех подзадач."""
        subtasks = SubTask.objects.all().select_related('task')

        # Фильтрация по задаче
        task_id = request.query_params.get('task_id')
        if task_id:
            subtasks = subtasks.filter(task_id=task_id)

        # Фильтрация по статусу
        status_filter = request.query_params.get('status')
        if status_filter:
            subtasks = subtasks.filter(status=status_filter)

        # Поиск
        search = request.query_params.get('search')
        if search:
            subtasks = subtasks.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Сортировка
        ordering = request.query_params.get('ordering', '-created_at')
        if ordering:
            subtasks = subtasks.order_by(ordering)

        serializer = SubTaskSerializer(subtasks, many=True)
        return Response({
            'count': subtasks.count(),
            'results': serializer.data
        })

    def post(self, request):
        """Создание новой подзадачи."""
        serializer = SubTaskCreateSerializer(data=request.data)
        if serializer.is_valid():
            subtask = serializer.save()
            response_serializer = SubTaskSerializer(subtask)
            return Response(
                {
                    'message': 'Подзадача успешно создана',
                    'subtask': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubTaskDetailUpdateDeleteView(APIView):
    """
    Представление для получения, обновления и удаления подзадач.

    GET /api/subtasks/{id}/ - получить подзадачу по ID
    PUT /api/subtasks/{id}/ - полное обновление подзадачи
    PATCH /api/subtasks/{id}/ - частичное обновление подзадачи
    DELETE /api/subtasks/{id}/ - удаление подзадачи
    """

    def get_object(self, id):
        """Получение объекта подзадачи или возврат 404."""
        return get_object_or_404(SubTask, id=id)

    def get(self, request, id):
        """Получение конкретной подзадачи."""
        subtask = self.get_object(id)
        serializer = SubTaskSerializer(subtask)
        return Response(serializer.data)

    def put(self, request, id):
        """Полное обновление подзадачи."""
        subtask = self.get_object(id)
        serializer = SubTaskUpdateSerializer(subtask, data=request.data)
        if serializer.is_valid():
            updated_subtask = serializer.save()
            response_serializer = SubTaskSerializer(updated_subtask)
            return Response({
                'message': 'Подзадача успешно обновлена',
                'subtask': response_serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        """Частичное обновление подзадачи."""
        subtask = self.get_object(id)
        serializer = SubTaskUpdateSerializer(subtask, data=request.data, partial=True)
        if serializer.is_valid():
            updated_subtask = serializer.save()
            response_serializer = SubTaskSerializer(updated_subtask)
            return Response({
                'message': 'Подзадача успешно обновлена',
                'subtask': response_serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        """Удаление подзадачи."""
        subtask = self.get_object(id)
        task_title = subtask.task.title
        subtask_title = subtask.title
        subtask.delete()
        return Response({
            'message': f'Подзадача "{subtask_title}" задачи "{task_title}" успешно удалена'
        }, status=status.HTTP_204_NO_CONTENT)


# Представления для работы с категориями

class CategoryListCreateAPIView(generics.ListCreateAPIView):
    """
    Эндпоинт для получения списка категорий и создания новых.

    GET /api/categories/
    POST /api/categories/
    """
    queryset = Category.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CategoryCreateSerializer
        return CategorySerializer


class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Эндпоинт для получения, обновления и удаления категории.

    GET /api/categories/{id}/
    PUT /api/categories/{id}/
    DELETE /api/categories/{id}/
    """
    queryset = Category.objects.all()
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CategoryCreateSerializer
        return CategorySerializer


@api_view(['GET'])
def task_statistics_view(request):
    """
    Агрегирующий эндпоинт для получения статистики задач.

    GET /api/tasks/statistics/
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

    # Средний процент выполнения задач
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


# Дополнительные представления для удобства

@api_view(['POST'])
def bulk_update_subtasks_status(request):
    """
    Массовое обновление статуса подзадач.

    POST /api/subtasks/bulk-update-status/
    Body: {
        "subtask_ids": [1, 2, 3],
        "status": "done"
    }
    """
    subtask_ids = request.data.get('subtask_ids', [])
    new_status = request.data.get('status')

    if not subtask_ids or not new_status:
        return Response(
            {'error': 'Необходимо указать subtask_ids и status'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if new_status not in ['new', 'in_progress', 'pending', 'blocked', 'done']:
        return Response(
            {'error': 'Неверный статус'},
            status=status.HTTP_400_BAD_REQUEST
        )

    updated_count = SubTask.objects.filter(id__in=subtask_ids).update(status=new_status)

    return Response({
        'message': f'Статус {updated_count} подзадач обновлен на "{new_status}"',
        'updated_count': updated_count
    })

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