import logging

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Ticket
from .stats import clear_statistics_cache
from .tasks import notify_urgent_ticket

logger = logging.getLogger(__name__)


def _send_urgent_notification(ticket_id):
    try:
        notify_urgent_ticket.delay(ticket_id)
    except Exception:
        logger.exception("Urgent ticket vazifasini navbatga qo'yib bo'lmadi: ticket=%s", ticket_id)


@receiver(post_save, sender=Ticket)
def ticket_saved(sender, instance, created, **kwargs):
    clear_statistics_cache()
    if created and instance.priority == Ticket.Priority.URGENT:
        transaction.on_commit(lambda: _send_urgent_notification(instance.pk))


@receiver(post_delete, sender=Ticket)
def ticket_deleted(sender, instance, **kwargs):
    clear_statistics_cache()
