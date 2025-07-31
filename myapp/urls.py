from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello_view, name='hello'),
    path('tasks/', views.tasks_view, name='tasks'),
]