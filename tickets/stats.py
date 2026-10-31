import logging

from django.core.cache import cache
from django.db.models import Count, Q

from .models import Ticket

logger = logging.getLogger(__name__)

CACHE_KEY = "tickets:statistics"
CACHE_TIMEOUT = 60 * 5


def calculate_statistics():
    return Ticket.objects.aggregate(
        total=Count("id"),
        new=Count("id", filter=Q(status=Ticket.Status.NEW)),
        in_progress=Count("id", filter=Q(status=Ticket.Status.IN_PROGRESS)),
        resolved=Count("id", filter=Q(status=Ticket.Status.RESOLVED)),
        closed=Count("id", filter=Q(status=Ticket.Status.CLOSED)),
        urgent=Count("id", filter=Q(priority=Ticket.Priority.URGENT)),
    )


def get_statistics():
    try:
        cached = cache.get(CACHE_KEY)
    except Exception:
        logger.warning("Redis ishlamayapti, statistika bazadan olindi", exc_info=True)
        return calculate_statistics()

    if cached is not None:
        return cached

    data = calculate_statistics()
    try:
        cache.set(CACHE_KEY, data, CACHE_TIMEOUT)
    except Exception:
        logger.warning("Statistikani cache'ga yozib bo'lmadi", exc_info=True)
    return data


def clear_statistics_cache():
    try:
        cache.delete(CACHE_KEY)
    except Exception:
        logger.warning("Statistika cache'sini tozalab bo'lmadi", exc_info=True)
