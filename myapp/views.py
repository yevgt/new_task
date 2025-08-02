from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters, permissions, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
from django.utils import timezone
import calendar
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


# def tasks_view(request):
#     tasks = Task.objects.all().prefetch_related('categories', 'subtasks')
#     categories = Category.objects.all()
#
#     context = {
#         'tasks': tasks,
#         'categories': categories,
#     }
#     return render(request, 'myapp/tasks.html', context)


# Кастомная пагинация для подзадач (Задание 2)
class SubTaskPagination(PageNumberPagination):
    """Кастомная пагинация для подзадач - 5 объектов на страницу."""
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50


# REST API представления для задач

class TaskListCreateAPIView(generics.ListCreateAPIView):
    """
    Эндпоинт для создания и получения списка задач.

    GET /tasks/ - получить список задач с фильтрацией, поиском и сортировкой
    POST /tasks/ - создать новую задачу

    Параметры фильтрации:
    - status: фильтр по статусу
    - is_overdue: фильтр просроченных задач (true/false)
    - categories: фильтр по категориям (ID категории)
    - search: поиск по названию и описанию
    - ordering: сортировка (по умолчанию -created_at)
    """
    queryset = Task.objects.all().prefetch_related('categories', 'subtasks')

    # Бэкенды для отображения полей в DRF интерфейсе
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Поля для поиска (отобразятся в интерфейсе)
    search_fields = ['title', 'description']

    # Поля для сортировки (отобразятся в интерфейсе)
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    # Простая фильтрация (отобразится в интерфейсе)
    filterset_fields = ['status', 'deadline']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateSerializer
        return TaskListSerializer

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

        def list(self, request, *args, **kwargs):
            queryset = self.get_queryset()

        # Информация о примененных фильтрах
        filter_info = {}
        status_filter = request.query_params.get('status')
        deadline_filter = request.query_params.get('deadline')
        deadline_from = request.query_params.get('deadline_from')
        deadline_to = request.query_params.get('deadline_to')
        is_overdue = request.query_params.get('is_overdue')
        category_id = request.query_params.get('categories')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering', '-created_at')

        if status_filter:
            filter_info['filtered_by_status'] = status_filter
        if deadline_filter:
            filter_info['filtered_by_deadline'] = deadline_filter
        if deadline_from:
            filter_info['deadline_from'] = deadline_from
        if deadline_to:
            filter_info['deadline_to'] = deadline_to
        if is_overdue:
            filter_info['is_overdue'] = is_overdue
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                filter_info['filtered_by_category'] = category.name
            except Category.DoesNotExist:
                pass
        if search:
            filter_info['search_query'] = search

        filter_info['ordering'] = ordering

        if len([k for k in filter_info.keys() if k != 'ordering']) == 0:
            filter_info['showing'] = 'Все задачи'

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['filter_info'] = filter_info
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'filter_info': filter_info,
            'count': queryset.count(),
            'results': serializer.data
        })

class TaskRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
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


# Задание 1: Эндпоинт для получения задач по дню недели
class TaskListByWeekdayAPIView(generics.ListAPIView):
    """
    Эндпоинт для получения списка задач по дню недели.

    GET /api/tasks/by-weekday/

    Параметры запроса:
    - weekday: день недели (monday, tuesday, wednesday, thursday, friday, saturday, sunday)
    - weekday_num: день недели числом (1=понедельник, 2=вторник, ..., 7=воскресенье)
    - status: фильтр по статусу
    - search: поиск по названию и описанию
    - ordering: сортировка (по умолчанию -created_at)
    """
    serializer_class = TaskListSerializer

    def get_queryset(self):
        queryset = Task.objects.all().prefetch_related('categories', 'subtasks')

        # Словарь для преобразования названий дней в номера
        weekday_mapping = {
            'monday': 1, 'mon': 1,
            'tuesday': 2, 'tue': 2, 'tues': 2,
            'wednesday': 3, 'wed': 3,
            'thursday': 4, 'thu': 4, 'thur': 4, 'thurs': 4,
            'friday': 5, 'fri': 5,
            'saturday': 6, 'sat': 6,
            'sunday': 7, 'sun': 7,
        }

        # Фильтрация по дню недели (название)
        weekday = self.request.query_params.get('weekday', '').lower()
        if weekday and weekday in weekday_mapping:
            weekday_num = weekday_mapping[weekday]
            queryset = queryset.extra(
                where=["EXTRACT(dow FROM deadline) = %s"],
                params=[weekday_num % 7]  # PostgreSQL использует 0=воскресенье, 6=суббота
            )

        # Фильтрация по дню недели (число)
        weekday_num = self.request.query_params.get('weekday_num')
        if weekday_num:
            try:
                weekday_num = int(weekday_num)
                if 1 <= weekday_num <= 7:
                    # Преобразуем: 1=понедельник -> 1 (PostgreSQL), 7=воскресенье -> 0 (PostgreSQL)
                    pg_weekday = weekday_num % 7
                    queryset = queryset.extra(
                        where=["EXTRACT(dow FROM deadline) = %s"],
                        params=[pg_weekday]
                    )
            except ValueError:
                pass

        # Дополнительные фильтры
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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Добавляем информацию о фильтре в ответ
        weekday = request.query_params.get('weekday', '').lower()
        weekday_num = request.query_params.get('weekday_num')

        filter_info = {}
        if weekday:
            filter_info['filtered_by_weekday'] = weekday.title()
        elif weekday_num:
            try:
                weekday_num = int(weekday_num)
                if 1 <= weekday_num <= 7:
                    weekday_names = ['', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота',
                                     'Воскресенье']
                    filter_info['filtered_by_weekday'] = weekday_names[weekday_num]
            except ValueError:
                pass

        if not filter_info:
            filter_info['showing'] = 'Все задачи'

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['filter_info'] = filter_info
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'filter_info': filter_info,
            'count': queryset.count(),
            'results': serializer.data
        })


# Задание 2: Generic Views для подзадач
class SubTaskListCreateAPIView(generics.ListCreateAPIView):
    """
    Эндпоинт для создания и получения списка подзадач.

    GET /subtasks/ - получить список подзадач с фильтрацией, поиском и сортировкой
    POST /subtasks/ - создать новую подзадачу

    Параметры фильтрации:
    - task_title: название главной задачи (частичное совпадение)
    - task_title_exact: точное название главной задачи
    - task_id: ID главной задачи
    - status: статус подзадачи
    - search: поиск по названию и описанию
    - ordering: сортировка (по умолчанию -created_at)
    """
    queryset = SubTask.objects.all().select_related('task')
    pagination_class = SubTaskPagination

    # Бэкенды для отображения полей в DRF интерфейсе
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Поля для поиска (отобразятся в интерфейсе)
    search_fields = ['title', 'description']

    # Поля для сортировки (отобразятся в интерфейсе)
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    # Простая фильтрация (отобразится в интерфейсе)
    filterset_fields = ['status', 'deadline']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SubTaskCreateSerializer
        return SubTaskSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация по названию главной задачи (частичное совпадение)
        task_title = self.request.query_params.get('task_title')
        if task_title:
            queryset = queryset.filter(task__title__icontains=task_title)

        # Фильтрация по точному названию главной задачи
        task_title_exact = self.request.query_params.get('task_title_exact')
        if task_title_exact:
            queryset = queryset.filter(task__title__iexact=task_title_exact)

        # Фильтрация по задаче
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        # Фильтрация по статусу
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Фильтрация по дедлайну
        deadline_filter = self.request.query_params.get('deadline')
        if deadline_filter:
            queryset = queryset.filter(deadline__date=deadline_filter)

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

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Информация о примененных фильтрах
        filter_info = {}
        task_title = request.query_params.get('task_title')
        task_title_exact = request.query_params.get('task_title_exact')
        task_id = request.query_params.get('task_id')
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search')

        if task_title:
            filter_info['filtered_by_task_title'] = task_title
        if task_title_exact:
            filter_info['filtered_by_exact_task_title'] = task_title_exact
        if task_id:
            try:
                task = Task.objects.get(id=task_id)
                filter_info['filtered_by_task'] = task.title
            except Task.DoesNotExist:
                pass
        if status_filter:
            filter_info['filtered_by_status'] = status_filter
        if search:
            filter_info['search_query'] = search

        if not filter_info:
            filter_info['showing'] = 'Все подзадачи'

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['filter_info'] = filter_info
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'filter_info': filter_info,
            'count': queryset.count(),
            'results': serializer.data
        })


class SubTaskRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Эндпоинт для получения, обновления и удаления подзадач.

    GET /subtasks/{id}/ - получить подзадачу по ID
    PUT /subtasks/{id}/ - полное обновление подзадачи
    PATCH /subtasks/{id}/ - частичное обновление подзадачи
    DELETE /subtasks/{id}/ - удаление подзадачи
    """
    queryset = SubTask.objects.all().select_related('task')
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SubTaskUpdateSerializer
        return SubTaskSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            updated_subtask = serializer.save()
            response_serializer = SubTaskSerializer(updated_subtask)
            return Response({
                'message': 'Подзадача успешно обновлена',
                'subtask': response_serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        task_title = instance.task.title
        subtask_title = instance.title
        self.perform_destroy(instance)
        return Response({
            'message': f'Подзадача "{subtask_title}" задачи "{task_title}" успешно удалена'
        }, status=status.HTTP_204_NO_CONTENT)


# # Представления для работы с категориями
# class CategoryListCreateAPIView(generics.ListCreateAPIView):
#     """
#     Эндпоинт для получения списка категорий и создания новых.
#
#     GET /api/categories/
#     POST /api/categories/
#     """
#     queryset = Category.objects.all()
#
#     def get_serializer_class(self):
#         if self.request.method == 'POST':
#             return CategoryCreateSerializer
#         return CategorySerializer
#
#
# class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
#     """
#     Эндпоинт для получения, обновления и удаления категории.
#
#     GET /api/categories/{id}/
#     PUT /api/categories/{id}/
#     PATCH /api/categories/{id}/
#     DELETE /api/categories/{id}/
#     """
#     queryset = Category.objects.all()
#     lookup_field = 'id'
#
#     def get_serializer_class(self):
#         if self.request.method in ['PUT', 'PATCH']:
#             return CategoryCreateSerializer
#         return CategorySerializer
#
#
# Функциональные представления и дополнительные эндпоинты
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

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с категориями.

    list: GET /api/categories/ - получить список всех категорий
    create: POST /api/categories/ - создать новую категорию
    retrieve: GET /api/categories/{id}/ - получить конкретную категорию
    update: PUT /api/categories/{id}/ - полностью обновить категорию
    partial_update: PATCH /api/categories/{id}/ - частично обновить категорию
    destroy: DELETE /api/categories/{id}/ - удалить категорию
    count_tasks: GET /api/categories/count_tasks/ - подсчет задач для всех категорий
    """
    queryset = Category.objects.all()
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateSerializer
        return CategorySerializer

    @action(detail=False, methods=['get'])
    def count_tasks(self, request):
        """
        Кастомный метод для подсчета количества задач, связанных с каждой категорией.

        GET /api/categories/count_tasks/

        Возвращает список категорий с количеством связанных задач.
        """
        categories_with_counts = Category.objects.annotate(
            tasks_count=Count('tasks', distinct=True),
            active_tasks_count=Count('tasks', filter=Q(tasks__status__in=['new', 'in_progress', 'pending']),
                                     distinct=True),
            completed_tasks_count=Count('tasks', filter=Q(tasks__status='done'), distinct=True),
            overdue_tasks_count=Count(
                'tasks',
                filter=Q(tasks__deadline__lt=timezone.now()) & ~Q(tasks__status='done'),
                distinct=True
            )
        ).order_by('name')

        results = []
        for category in categories_with_counts:
            results.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'color': getattr(category, 'color', None),  # Если есть поле color
                'tasks_count': category.tasks_count,
                'active_tasks_count': category.active_tasks_count,
                'completed_tasks_count': category.completed_tasks_count,
                'overdue_tasks_count': category.overdue_tasks_count,
                'completion_percentage': round(
                    (category.completed_tasks_count / category.tasks_count * 100)
                    if category.tasks_count > 0 else 0, 2
                )
            })

        return Response({
            'message': 'Статистика задач по категориям',
            'total_categories': len(results),
            'categories': results
        })

    def create(self, request, *args, **kwargs):
        """Переопределяем создание для кастомного ответа"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            response_serializer = CategorySerializer(category)
            return Response(
                {
                    'message': 'Категория успешно создана',
                    'category': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Переопределяем обновление для кастомного ответа"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            updated_category = serializer.save()
            response_serializer = CategorySerializer(updated_category)
            return Response({
                'message': 'Категория успешно обновлена',
                'category': response_serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Переопределяем удаление для кастомного ответа"""
        instance = self.get_object()
        category_name = instance.name
        tasks_count = instance.tasks.count()

        # Проверяем, есть ли связанные задачи
        if tasks_count > 0:
            return Response({
                'error': f'Нельзя удалить категорию "{category_name}", так как с ней связано {tasks_count} задач(и)'
            }, status=status.HTTP_400_BAD_REQUEST)

        self.perform_destroy(instance)
        return Response({
            'message': f'Категория "{category_name}" успешно удалена'
        }, status=status.HTTP_204_NO_CONTENT)

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


@api_view(['GET'])
def weekday_info_view(request):
    """
    Эндпоинт для получения информации о доступных днях недели.

    GET /api/weekdays/
    """
    weekdays = [
        {'number': 1, 'name': 'monday', 'display_name': 'Понедельник', 'short': 'mon'},
        {'number': 2, 'name': 'tuesday', 'display_name': 'Вторник', 'short': 'tue'},
        {'number': 3, 'name': 'wednesday', 'display_name': 'Среда', 'short': 'wed'},
        {'number': 4, 'name': 'thursday', 'display_name': 'Четверг', 'short': 'thu'},
        {'number': 5, 'name': 'friday', 'display_name': 'Пятница', 'short': 'fri'},
        {'number': 6, 'name': 'saturday', 'display_name': 'Суббота', 'short': 'sat'},
        {'number': 7, 'name': 'sunday', 'display_name': 'Воскресенье', 'short': 'sun'},
    ]

    return Response({
        'weekdays': weekdays,
        'usage_examples': [
            '/api/tasks/by-weekday/?weekday=monday',
            '/api/tasks/by-weekday/?weekday_num=1',
            '/api/tasks/by-weekday/?weekday=friday&status=in_progress'
        ]
    })