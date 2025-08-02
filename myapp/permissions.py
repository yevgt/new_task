from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Кастомный пермишен: объект может редактировать только его владелец.
    """

    def has_object_permission(self, request, view, obj):
        # Права на чтение для всех аутентифицированных пользователей
        if request.method in permissions.SAFE_METHODS:
            return True

        # Права на запись только для владельца объекта
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # Если нет поля владельца, разрешаем всем аутентифицированным пользователям
        return request.user and request.user.is_authenticated


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Кастомный пермишен: только администраторы могут изменять, остальные только читать.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Кастомный пермишен: объект может редактировать владелец или администратор.
    """

    def has_object_permission(self, request, view, obj):
        # Администраторы могут всё
        if request.user and request.user.is_staff:
            return True

        # Владелец может редактировать свои объекты
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user

        return False


class IsAuthenticatedOrCreateOnly(permissions.BasePermission):
    """
    Пермишен для регистрации: анонимные пользователи могут только создавать аккаунты.
    """

    def has_permission(self, request, view):
        if request.method == 'POST':  # Создание аккаунта
            return True
        return request.user and request.user.is_authenticated


class IsOwner(permissions.BasePermission):
    """
    Пользовательский пермишен, который позволяет доступ только владельцам объекта.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTaskOwnerOrReadOnly(permissions.BasePermission):
    """
    Пермишен для подзадач: проверяет владельца основной задачи.
    """

    def has_object_permission(self, request, view, obj):
        # Безопасные методы разрешены всем аутентифицированным пользователям
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для подзадач проверяем владельца основной задачи
        if hasattr(obj, 'task'):
            return obj.task.owner == request.user

        # Для задач проверяем владельца
        return obj.owner == request.user