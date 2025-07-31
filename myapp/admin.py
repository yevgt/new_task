from django.contrib import admin
from .models import Task, SubTask, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 1
    fields = ['title', 'description', 'status', 'deadline']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'deadline', 'created_at', 'is_overdue']
    list_filter = ['status', 'categories', 'created_at', 'deadline']
    search_fields = ['title', 'description']
    filter_horizontal = ['categories']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    inlines = [SubTaskInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'categories')
        }),
        ('Статус и сроки', {
            'fields': ('status', 'deadline')
        }),
    )

    def is_overdue(self, obj):
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = 'Просрочена'


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task', 'status', 'deadline', 'created_at', 'is_overdue']
    list_filter = ['status', 'task', 'created_at', 'deadline']
    search_fields = ['title', 'description', 'task__title']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'task')
        }),
        ('Статус и сроки', {
            'fields': ('status', 'deadline')
        }),
    )

    def is_overdue(self, obj):
        return obj.is_overdue

    is_overdue.boolean = True
    is_overdue.short_description = 'Просрочена'