from unittest import mock

import pytest
from django.urls import reverse

from tickets.stats import CACHE_KEY

pytestmark = pytest.mark.django_db


def test_statistics_values(api_as, admin_user, make_ticket):
    make_ticket(status="new", priority="urgent")
    make_ticket(status="in_progress")
    make_ticket(status="resolved")
    make_ticket(status="closed")

    response = api_as(admin_user).get(reverse("ticket-statistics"))
    assert response.status_code == 200
    assert response.data == {
        "total": 4,
        "new": 1,
        "in_progress": 1,
        "resolved": 1,
        "closed": 1,
        "urgent": 1,
    }


def test_statistics_are_cached(api_as, admin_user, make_ticket, django_assert_num_queries):
    make_ticket()
    api = api_as(admin_user)
    url = reverse("ticket-statistics")

    first = api.get(url)
    with django_assert_num_queries(0):
        second = api.get(url)
    assert first.data == second.data


def test_cache_cleared_when_ticket_created(api_as, admin_user, client_user, category, make_ticket):
    make_ticket()
    api = api_as(admin_user)
    url = reverse("ticket-statistics")
    assert api.get(url).data["total"] == 1

    response = api_as(client_user).post(
        reverse("ticket-list"),
        {"title": "Yangi", "description": "Tavsif", "category": category.id},
        format="json",
    )
    assert response.status_code == 201
    assert api.get(url).data["total"] == 2


def test_cache_cleared_when_status_changes(api_as, admin_user, make_ticket):
    ticket = make_ticket()
    api = api_as(admin_user)
    url = reverse("ticket-statistics")
    assert api.get(url).data["new"] == 1

    api.patch(reverse("ticket-detail", args=[ticket.id]), {"status": "in_progress"}, format="json")
    data = api.get(url).data
    assert data["new"] == 0
    assert data["in_progress"] == 1


def test_statistics_work_when_redis_is_down(api_as, admin_user, make_ticket):
    make_ticket()
    error = ConnectionError("redis yo'q")
    with mock.patch("tickets.stats.cache.get", side_effect=error), mock.patch(
        "tickets.stats.cache.set", side_effect=error
    ):
        response = api_as(admin_user).get(reverse("ticket-statistics"))
    assert response.status_code == 200
    assert response.data["total"] == 1


def test_ticket_creation_survives_cache_failure(api_as, client_user, category):
    with mock.patch("tickets.stats.cache.delete", side_effect=ConnectionError("redis yo'q")):
        response = api_as(client_user).post(
            reverse("ticket-list"),
            {"title": "Test", "description": "Tavsif", "category": category.id},
            format="json",
        )
    assert response.status_code == 201


def test_client_cannot_see_statistics(api_as, client_user):
    assert api_as(client_user).get(reverse("ticket-statistics")).status_code == 403


def test_cache_key_is_set(api_as, admin_user):
    from django.core.cache import cache

    api_as(admin_user).get(reverse("ticket-statistics"))
    assert cache.get(CACHE_KEY) is not None
