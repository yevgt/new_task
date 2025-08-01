from django.urls import path
from .views import (
    TaskCreateAPIView,
    TaskListAPIView,
    TaskListByWeekdayAPIView,  # Новый эндпоинт для задач по дням недели
    TaskDetailAPIView,
    CategoryListCreateAPIView,
    CategoryDetailAPIView,
    SubTaskListCreateView,
    SubTaskDetailUpdateDeleteView,
    task_statistics_view,
    bulk_update_subtasks_status,
    weekday_info_view  # Новый эндпоинт для информации о днях недели
)

urlpatterns = [
    # Эндпоинты для задач
    path('tasks/create/', TaskCreateAPIView.as_view(), name='task-create'),
    path('tasks/', TaskListAPIView.as_view(), name='task-list'),
    path('tasks/by-weekday/', TaskListByWeekdayAPIView.as_view(), name='task-list-by-weekday'),  # Задание 1
    path('tasks/<int:id>/', TaskDetailAPIView.as_view(), name='task-detail'),
    path('tasks/statistics/', task_statistics_view, name='task-statistics'),

    # Эндпоинты для подзадач (Задания 2 и 3)
    path('subtasks/', SubTaskListCreateView.as_view(), name='subtask-list-create'),
    path('subtasks/<int:id>/', SubTaskDetailUpdateDeleteView.as_view(), name='subtask-detail'),
    path('subtasks/bulk-update-status/', bulk_update_subtasks_status, name='subtask-bulk-update'),

    # Эндпоинты для категорий
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<int:id>/', CategoryDetailAPIView.as_view(), name='category-detail'),

    # Дополнительные эндпоинты
    path('weekdays/', weekday_info_view, name='weekday-info'),
]