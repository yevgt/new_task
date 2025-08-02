import logging
from datetime import datetime
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from .auth_serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)

logger = logging.getLogger('myapp')


class UserRegistrationView(generics.CreateAPIView):
    """Представление для регистрации пользователя"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()

                # Создаем JWT токены для нового пользователя
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                response_data = {
                    'message': 'Пользователь успешно зарегистрирован',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    },
                    'access': str(access_token),
                    'refresh': str(refresh),
                }

                response = Response(response_data, status=status.HTTP_201_CREATED)

                # Устанавливаем cookies с токенами
                response.set_cookie(
                    'access_token',
                    str(access_token),
                    max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    secure=settings.DEBUG is False,  # HTTPS в продакшене
                    samesite='Lax'
                )
                response.set_cookie(
                    'refresh_token',
                    str(refresh),
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    secure=settings.DEBUG is False,
                    samesite='Lax'
                )

                logger.info(f"User '{user.username}' registered successfully")
                return response

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Registration error: {e}")
            return Response(
                {'error': 'Ошибка при регистрации пользователя'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """Кастомное представление для получения JWT токенов"""
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                tokens_data = serializer.validated_data

                response = Response({
                    'message': 'Вход выполнен успешно',
                    'user': tokens_data['user'],
                    'access': tokens_data['access'],
                    'refresh': tokens_data['refresh'],
                }, status=status.HTTP_200_OK)

                # Устанавливаем cookies с токенами
                response.set_cookie(
                    'access_token',
                    tokens_data['access'],
                    max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    secure=settings.DEBUG is False,
                    samesite='Lax'
                )
                response.set_cookie(
                    'refresh_token',
                    tokens_data['refresh'],
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    secure=settings.DEBUG is False,
                    samesite='Lax'
                )

                logger.info(f"User '{serializer.user.username}' logged in successfully")
                return response

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Login error: {e}")
            return Response(
                {'error': 'Ошибка при входе в систему'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomTokenRefreshView(TokenRefreshView):
    """Кастомное представление для обновления токенов"""

    def post(self, request, *args, **kwargs):
        try:
            # Пытаемся получить refresh токен из cookies
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                refresh_token = request.data.get('refresh')

            if not refresh_token:
                return Response(
                    {'error': 'Refresh token не найден'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Подставляем токен в данные запроса
            request.data['refresh'] = refresh_token

            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                # Обновляем cookie с новым access токеном
                response.set_cookie(
                    'access_token',
                    response.data['access'],
                    max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    secure=settings.DEBUG is False,
                    samesite='Lax'
                )

                # Если есть новый refresh токен, обновляем и его
                if 'refresh' in response.data:
                    response.set_cookie(
                        'refresh_token',
                        response.data['refresh'],
                        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                        httponly=True,
                        secure=settings.DEBUG is False,
                        samesite='Lax'
                    )

            return response

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return Response(
                {'error': 'Ошибка при обновлении токена'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Представление для выхода из системы"""
    try:
        # Получаем refresh токен из cookies или тела запроса
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            refresh_token = request.data.get('refresh')

        if refresh_token:
            try:
                # Добавляем токен в blacklist
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"User '{request.user.username}' logged out - token blacklisted")
            except TokenError as e:
                logger.warning(f"Token blacklist error: {e}")

        # Создаем ответ
        response = Response({
            'message': 'Выход выполнен успешно'
        }, status=status.HTTP_200_OK)

        # Удаляем cookies с токенами
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return Response(
            {'error': 'Ошибка при выходе из системы'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_view(request):
    """Получение профиля текущего пользователя"""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request):
    """Смена пароля пользователя"""
    try:
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            # Проверяем старый пароль
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': 'Неверный текущий пароль'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Устанавливаем новый пароль
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            # Инвалидируем все существующие токены пользователя
            outstanding_tokens = OutstandingToken.objects.filter(user=user)
            for token in outstanding_tokens:
                try:
                    BlacklistedToken.objects.get_or_create(token=token)
                except:
                    pass

            logger.info(f"Password changed for user '{user.username}'")

            return Response({
                'message': 'Пароль успешно изменен. Необходимо войти заново.'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Change password error: {e}")
        return Response(
            {'error': 'Ошибка при смене пароля'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )