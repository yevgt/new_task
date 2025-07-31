from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),

    # Добавляем browsable API для удобства разработки
    path('api-auth/', include('rest_framework.urls')),
]
