from django.urls import path
from .views import (
    TaskCreateAPIView,
    TaskListAPIView,
    TaskDetailAPIView,
    CategoryListAPIView,
    task_statistics_view
)

urlpatterns = [
    # Эндпоинты для задач
    path('tasks/create/', TaskCreateAPIView.as_view(), name='task-create'),
    path('tasks/', TaskListAPIView.as_view(), name='task-list'),
    path('tasks/<int:id>/', TaskDetailAPIView.as_view(), name='task-detail'),
    path('tasks/statistics/', task_statistics_view, name='task-statistics'),

    # Эндпоинты для категорий
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
]