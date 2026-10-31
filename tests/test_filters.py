from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from tickets.models import Ticket

pytestmark = pytest.mark.django_db


def ids(response):
    return [item["id"] for item in response.data["results"]]


def test_search_by_title_and_description(api_as, admin_user, make_ticket):
    internet = make_ticket(title="Internet sekin", description="Tezlik past")
    printer = make_ticket(title="Printer", description="Qog'oz tiqilib qoldi")
    api = api_as(admin_user)

    assert ids(api.get(reverse("ticket-list"), {"search": "internet"})) == [internet.id]
    assert ids(api.get(reverse("ticket-list"), {"search": "qog'oz"})) == [printer.id]


def test_filter_by_status_and_priority(api_as, admin_user, make_ticket):
    make_ticket(status="new", priority="low")
    target = make_ticket(status="in_progress", priority="urgent")
    make_ticket(status="in_progress", priority="low")
    api = api_as(admin_user)

    assert len(ids(api.get(reverse("ticket-list"), {"status": "in_progress"}))) == 2
    assert ids(api.get(reverse("ticket-list"), {"priority": "urgent"})) == [target.id]
    assert ids(api.get(reverse("ticket-list"), {"status": "in_progress", "priority": "urgent"})) == [target.id]


def test_filter_by_category_and_operator(api_as, admin_user, operator, category, make_ticket):
    from tickets.models import Category

    other_category = Category.objects.create(name="Taklif")
    first = make_ticket(operator=operator)
    make_ticket(category=other_category)
    api = api_as(admin_user)

    assert ids(api.get(reverse("ticket-list"), {"category": category.id})) == [first.id]
    assert ids(api.get(reverse("ticket-list"), {"operator": operator.id})) == [first.id]


def test_filter_by_date_range(api_as, admin_user, make_ticket):
    old = make_ticket(title="Eski")
    new = make_ticket(title="Yangi")
    Ticket.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=20))
    api = api_as(admin_user)
    today = timezone.localdate()

    response = api.get(reverse("ticket-list"), {"created_from": (today - timedelta(days=5)).isoformat()})
    assert ids(response) == [new.id]
    response = api.get(reverse("ticket-list"), {"created_to": (today - timedelta(days=5)).isoformat()})
    assert ids(response) == [old.id]


def test_ordering(api_as, admin_user, make_ticket):
    low = make_ticket(priority="low")
    urgent = make_ticket(priority="urgent")
    medium = make_ticket(priority="medium")
    api = api_as(admin_user)

    assert ids(api.get(reverse("ticket-list"), {"ordering": "-priority"})) == [urgent.id, medium.id, low.id]
    assert ids(api.get(reverse("ticket-list"), {"ordering": "priority"})) == [low.id, medium.id, urgent.id]
    assert ids(api.get(reverse("ticket-list"), {"ordering": "-created_at"})) == [medium.id, urgent.id, low.id]


def test_operator_gets_own_urgent_tickets_newest_first(api_as, operator, other_operator, make_ticket):
    first = make_ticket(operator=operator, priority="urgent")
    second = make_ticket(operator=operator, priority="urgent")
    make_ticket(operator=operator, priority="low")
    make_ticket(operator=other_operator, priority="urgent")

    response = api_as(operator).get(
        reverse("ticket-list"), {"priority": "urgent", "ordering": "-created_at"}
    )
    assert ids(response) == [second.id, first.id]


def test_filter_cannot_expose_foreign_tickets(api_as, client_user, other_client, make_ticket):
    make_ticket(client=other_client, priority="urgent")
    response = api_as(client_user).get(reverse("ticket-list"), {"priority": "urgent"})
    assert response.data["count"] == 0
