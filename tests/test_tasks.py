from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from tickets.models import Ticket
from tickets.tasks import notify_urgent_ticket, report_stale_new_tickets

pytestmark = pytest.mark.django_db


def test_urgent_ticket_sends_email_to_operator(operator, make_ticket, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        make_ticket(priority="urgent", operator=operator)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [operator.email]


def test_urgent_ticket_without_operator_goes_to_admin(admin_user, make_ticket, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        make_ticket(priority="urgent")
    assert mail.outbox[0].to == [admin_user.email]


def test_normal_ticket_sends_no_email(admin_user, make_ticket, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        make_ticket(priority="low")
    assert mail.outbox == []


def test_ticket_is_created_even_if_queue_is_down(client_user, category, django_capture_on_commit_callbacks):
    from unittest import mock

    with mock.patch.object(notify_urgent_ticket, "delay", side_effect=ConnectionError("broker yo'q")):
        with django_capture_on_commit_callbacks(execute=True):
            ticket = Ticket.objects.create(
                title="Test", description="Tavsif", client=client_user, category=category, priority="urgent"
            )
    assert Ticket.objects.filter(pk=ticket.pk).exists()


def test_stale_new_tickets_task(make_ticket):
    old = make_ticket()
    make_ticket()
    make_ticket(status="in_progress")
    Ticket.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(hours=30))
    assert report_stale_new_tickets() == 1
