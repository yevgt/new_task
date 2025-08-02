import re
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_username(self, value):
        """Валидация username"""
        if not value:
            raise serializers.ValidationError("Имя пользователя обязательно.")

        if len(value) < 3:
            raise serializers.ValidationError("Имя пользователя должно содержать минимум 3 символа.")

        if len(value) > 150:
            raise serializers.ValidationError("Имя пользователя не может превышать 150 символов.")

        # Проверка на допустимые символы
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                "Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_"
            )

        # Проверка уникальности
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")

        return value

    def validate_email(self, value):
        """Валидация email"""
        if not value:
            raise serializers.ValidationError("Email обязателен.")

        # Проверка уникальности
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")

        # Дополнительная проверка формата email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Введите корректный email адрес.")

        return value.lower()

    def validate_password(self, value):
        """Валидация пароля"""
        if not value:
            raise serializers.ValidationError("Пароль обязателен.")

        # Минимальная длина
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен содержать минимум 8 символов.")

        # Максимальная длина
        if len(value) > 128:
            raise serializers.ValidationError("Пароль не может превышать 128 символов.")

        # Проверка на наличие букв
        if not re.search(r'[a-zA-Z]', value):
            raise serializers.ValidationError("Пароль должен содержать хотя бы одну букву.")

        # Проверка на наличие цифр
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Пароль должен содержать хотя бы одну цифру.")

        # Проверка на наличие специальных символов
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Пароль должен содержать хотя бы один специальный символ.")

        # Использование встроенной валидации Django
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return value

    def validate(self, attrs):
        """Валидация всех полей"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Пароли не совпадают.'
            })

        return attrs

    def create(self, validated_data):
        """Создание пользователя"""
        # Удаляем password_confirm из данных
        validated_data.pop('password_confirm', None)

        # Создаем пользователя
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для получения JWT токенов"""

    def validate(self, attrs):
        # Получаем стандартные данные
        data = super().validate(attrs)

        # Добавляем информацию о пользователе
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'date_joined': self.user.date_joined,
        }

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_staff')
        read_only_fields = ('id', 'username', 'date_joined', 'is_staff')


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)

    def validate_new_password(self, value):
        """Валидация нового пароля"""
        # Применяем те же правила, что и при регистрации
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен содержать минимум 8 символов.")

        if not re.search(r'[a-zA-Z]', value):
            raise serializers.ValidationError("Пароль должен содержать хотя бы одну букву.")

        if not re.search(r'\d', value):
            raise serializers.ValidationError("Пароль должен содержать хотя бы одну цифру.")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Пароль должен содержать хотя бы один специальный символ.")

        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Новые пароли не совпадают.'
            })
        return attrs