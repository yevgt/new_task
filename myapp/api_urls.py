from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # TaskCreateAPIView,
    # TaskListAPIView,
    TaskListCreateAPIView,
    TaskListByWeekdayAPIView,  # Новый эндпоинт для задач по дням недели
    # TaskDetailAPIView,
    TaskRetrieveUpdateDestroyAPIView,

    #CategoryListCreateAPIView,
    # CategoryDetailAPIView,
    #CategoryRetrieveUpdateDestroyAPIView,
    CategoryViewSet,  # Заменяем старые представления на ViewSet

    # SubTaskListCreateView,
    SubTaskListCreateAPIView,
    # SubTaskDetailUpdateDeleteView,
    SubTaskRetrieveUpdateDestroyAPIView,
    task_statistics_view,
    bulk_update_subtasks_status,
    weekday_info_view  # Новый эндпоинт для информации о днях недели
)

from .auth_views import (
    UserRegistrationView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    logout_view,
    user_profile_view,
    change_password_view,
)

# Создаем роутер для ViewSet
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')

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
    # path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    # path('categories/<int:id>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category-detail'),
    # Включаем маршруты для CategoryViewSet
    path('', include(router.urls)),

    # Дополнительные эндпоинты
    path('weekdays/', weekday_info_view, name='weekday-info'),

# Аутентификация
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', logout_view, name='user-logout'),
    path('auth/profile/', user_profile_view, name='user-profile'),
    path('auth/change-password/', change_password_view, name='change-password'),
]