from django.apps import AppConfig


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    verbose_name = 'Todo App'

    def ready(self):
        import myapp.signals  # Подключаем сигналы
