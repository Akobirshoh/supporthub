import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from users.models import Role, User

from .models import Ticket

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def notify_urgent_ticket(self, ticket_id):
    logger.info("Urgent ticket xabarnomasi boshlandi: ticket=%s", ticket_id)
    ticket = Ticket.objects.select_related("operator", "client").filter(pk=ticket_id).first()
    if ticket is None:
        logger.warning("Ticket topilmadi: ticket=%s", ticket_id)
        return 0

    if ticket.operator and ticket.operator.email:
        recipients = [ticket.operator.email]
    else:
        recipients = list(
            User.objects.filter(role=Role.ADMIN, is_active=True)
            .exclude(email="")
            .values_list("email", flat=True)
        )

    if not recipients:
        logger.warning("Xabar yuboriladigan operator yoki admin topilmadi: ticket=%s", ticket_id)
        return 0

    try:
        send_mail(
            subject=f"Shoshilinch murojaat #{ticket.pk}: {ticket.title}",
            message=(
                f"Mijoz: {ticket.client.username}\n"
                f"Sarlavha: {ticket.title}\n\n"
                f"{ticket.description}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
        )
    except Exception as exc:
        logger.error("Xabar yuborishda xato: ticket=%s, xato=%r", ticket_id, exc)
        raise self.retry(exc=exc)

    logger.info("Urgent ticket xabarnomasi yuborildi: ticket=%s, qabul qiluvchilar=%s", ticket_id, len(recipients))
    return len(recipients)


@shared_task
def report_stale_new_tickets():
    border = timezone.now() - timedelta(hours=24)
    ids = list(
        Ticket.objects.filter(status=Ticket.Status.NEW, created_at__lt=border)
        .order_by("created_at")
        .values_list("id", flat=True)
    )
    if ids:
        logger.warning("24 soatdan ortiq 'new' holatida turgan ticketlar: soni=%s, id=%s", len(ids), ids)
    else:
        logger.info("24 soatdan ortiq 'new' holatida turgan ticket yo'q")
    return len(ids)
