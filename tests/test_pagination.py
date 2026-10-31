import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def many_tickets(make_ticket):
    for number in range(25):
        make_ticket(title=f"Murojaat {number}")


def test_pagination_structure(api_as, admin_user, many_tickets):
    response = api_as(admin_user).get(reverse("ticket-list"), {"page": 2, "page_size": 10})
    assert response.status_code == 200
    assert response.data["count"] == 25
    assert response.data["total_pages"] == 3
    assert response.data["current_page"] == 2
    assert response.data["page_size"] == 10
    assert len(response.data["results"]) == 10
    assert "page=3" in response.data["next"]
    assert response.data["previous"] is not None


def test_default_page_size_is_10(api_as, admin_user, many_tickets):
    response = api_as(admin_user).get(reverse("ticket-list"))
    assert response.data["page_size"] == 10
    assert len(response.data["results"]) == 10
    assert response.data["previous"] is None


def test_max_page_size_is_100(api_as, admin_user, many_tickets):
    response = api_as(admin_user).get(reverse("ticket-list"), {"page_size": 500})
    assert response.data["page_size"] == 100
    assert len(response.data["results"]) == 25


def test_invalid_page_returns_clear_error(api_as, admin_user, many_tickets):
    response = api_as(admin_user).get(reverse("ticket-list"), {"page": 99})
    assert response.status_code == 404
    assert "Mavjud sahifalar" in response.data["detail"]
    response = api_as(admin_user).get(reverse("ticket-list"), {"page": "abc"})
    assert response.status_code == 404
