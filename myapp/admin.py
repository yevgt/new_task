from django.contrib import admin
from .models import Task, SubTask, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 25


class SubTaskInline(admin.TabularInline):
    """Inline для отображения подзадач в задаче."""
    model = SubTask
    extra = 1
    fields = ['title', 'description', 'status', 'deadline']
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Административная панель для модели Task."""
    list_display = ['title', 'status', 'deadline', 'created_at', 'is_overdue', 'categories_list']
    list_filter = ['status', 'categories', 'created_at', 'deadline']
    search_fields = ['title', 'description']
    filter_horizontal = ['categories']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    inlines = [SubTaskInline]
    list_per_page = 25

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'categories'),
            'classes': ('wide',)
        }),
        ('Статус и сроки', {
            'fields': ('status', 'deadline'),
            'classes': ('wide',)
        }),
        ('Информация о создании', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at']

    def is_overdue(self, obj):
        """Отображение статуса просрочки в списке."""
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = 'Просрочена'

    def categories_list(self, obj):
        """Отображение списка категорий в списке задач."""
        return ", ".join([category.name for category in obj.categories.all()])

    categories_list.short_description = 'Категории'

@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    """Административная панель для модели SubTask."""
    list_display = ['title', 'task', 'status', 'deadline', 'created_at', 'is_overdue']
    list_filter = ['status', 'task', 'created_at', 'deadline']
    search_fields = ['title', 'description', 'task__title']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'task'),
            'classes': ('wide',)
        }),
        ('Статус и сроки', {
            'fields': ('status', 'deadline'),
            'classes': ('wide',)
        }),
        ('Информация о создании', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at']

    def is_overdue(self, obj):
        """Отображение статуса просрочки в списке."""
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = 'Просрочена'

    # Автозаполнение поля task
    autocomplete_fields = ['task']


# Дополнительные настройки админки
admin.site.site_header = "Task Manager Administration"
admin.site.site_title = "Task Manager Admin"
admin.site.index_title = "Добро пожаловать в панель управления Task Manager"