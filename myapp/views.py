from django.http import HttpResponse
from django.shortcuts import render
from .models import Task, Category


def hello_view(request):
    return HttpResponse("<h1>Hello, YevgeniyG</h1>")


def tasks_view(request):
    tasks = Task.objects.all().prefetch_related('categories', 'subtasks')
    categories = Category.objects.all()

    context = {
        'tasks': tasks,
        'categories': categories,
    }
    return render(request, 'myapp/tasks.html', context)

