from django.urls import path, include
from . import views

urlpatterns = [
    # Веб-интерфейс
    path('', views.hello_view, name='hello'),
    path('tasks/', views.tasks_view, name='tasks'),

    # API маршруты
    path('api/', include('myapp.api_urls')),
]