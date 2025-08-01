from django.urls import path
from .views import (
    # TaskCreateAPIView,
    # TaskListAPIView,
    TaskListCreateAPIView,
    TaskListByWeekdayAPIView,  # Новый эндпоинт для задач по дням недели
    # TaskDetailAPIView,
    TaskRetrieveUpdateDestroyAPIView,

    CategoryListCreateAPIView,
    # CategoryDetailAPIView,
    CategoryRetrieveUpdateDestroyAPIView,

    # SubTaskListCreateView,
    SubTaskListCreateAPIView,
    # SubTaskDetailUpdateDeleteView,
    SubTaskRetrieveUpdateDestroyAPIView,
    task_statistics_view,
    bulk_update_subtasks_status,
    weekday_info_view  # Новый эндпоинт для информации о днях недели
)

urlpatterns = [
    # Эндпоинты для задач
    # path('tasks/create/', TaskCreateAPIView.as_view(), name='task-create'),
    path('tasks/', TaskListCreateAPIView.as_view(), name='task-list-create'),  # GET для списка, POST для создания
    path('tasks/by-weekday/', TaskListByWeekdayAPIView.as_view(), name='task-list-by-weekday'),  # Задание 1
    path('tasks/<int:id>/', TaskRetrieveUpdateDestroyAPIView.as_view(), name='task-detail'),  # GET, PUT, PATCH, DELETE
    path('tasks/statistics/', task_statistics_view, name='task-statistics'),

    # Эндпоинты для подзадач (Задания 2 и 3)
    path('subtasks/', SubTaskListCreateAPIView.as_view(), name='subtask-list-create'),  # GET для списка, POST для создания
    path('subtasks/<int:id>/', SubTaskRetrieveUpdateDestroyAPIView.as_view(), name='subtask-detail'),  # GET, PUT, PATCH, DELETE
    path('subtasks/bulk-update-status/', bulk_update_subtasks_status, name='subtask-bulk-update'),

    # Эндпоинты для категорий
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<int:id>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category-detail'),

    # Дополнительные эндпоинты
    path('weekdays/', weekday_info_view, name='weekday-info'),
]