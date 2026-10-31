import logging
import time

from django.utils import timezone

logger = logging.getLogger("supporthub.requests")

SKIP_PREFIXES = ("/admin/", "/static/")


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "-")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = timezone.localtime()
        start = time.perf_counter()

        response = self.get_response(request)

        duration = time.perf_counter() - start
        response["X-Response-Time"] = f"{duration:.3f}s"

        if not request.path.startswith(SKIP_PREFIXES):
            user = getattr(request, "user", None)
            user_id = user.pk if user is not None and user.is_authenticated else "anonymous"
            logger.info(
                "User=%s | Method=%s | Path=%s | IP=%s | Status=%s | Duration=%.3fs | Time=%s",
                user_id,
                request.method,
                request.path,
                get_client_ip(request),
                response.status_code,
                duration,
                started_at.strftime("%Y-%m-%d %H:%M:%S"),
            )
        return response

    def process_exception(self, request, exception):
        if not request.path.startswith(SKIP_PREFIXES):
            logger.error(
                "Kutilmagan xato | Method=%s | Path=%s | IP=%s | Error=%r",
                request.method,
                request.path,
                get_client_ip(request),
                exception,
                exc_info=exception,
            )
        return None
