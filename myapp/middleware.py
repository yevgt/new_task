import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django.request')


class HTTPLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для детального логирования HTTP запросов.
    """

    def process_request(self, request):
        """Логируем входящий запрос"""
        request.start_time = time.time()

        # Получаем IP адрес
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Логируем запрос
        logger.info(
            f"REQUEST: {request.method} {request.get_full_path()} | "
            f"IP: {ip} | User: {request.user if hasattr(request, 'user') else 'Anonymous'} | "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
        )

    def process_response(self, request, response):
        """Логируем ответ"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            # Определяем уровень логирования по статус-коду
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO

            logger.log(
                log_level,
                f"RESPONSE: {request.method} {request.get_full_path()} | "
                f"Status: {response.status_code} | Duration: {duration:.3f}s | "
                f"Size: {len(response.content)} bytes"
            )

        return response

    def process_exception(self, request, exception):
        """Логируем исключения"""
        logger.error(
            f"EXCEPTION: {request.method} {request.get_full_path()} | "
            f"Error: {str(exception)} | Type: {type(exception).__name__}",
            exc_info=True
        )