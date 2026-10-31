import pytest
from django.urls import reverse

from tickets.models import Category

pytestmark = pytest.mark.django_db


def test_admin_can_create_category(api_as, admin_user):
    response = api_as(admin_user).post(
        reverse("category-list"), {"name": "To'lov muammosi", "description": "Pul o'tkazmalari"}, format="json"
    )
    assert response.status_code == 201
    assert Category.objects.filter(name="To'lov muammosi").exists()


def test_client_cannot_create_category(api_as, client_user):
    response = api_as(client_user).post(reverse("category-list"), {"name": "Taklif"}, format="json")
    assert response.status_code == 403
    assert not Category.objects.filter(name="Taklif").exists()


def test_authenticated_user_can_list_categories(api_as, client_user, category):
    response = api_as(client_user).get(reverse("category-list"))
    assert response.status_code == 200
    assert response.data["count"] == 1


def test_duplicate_category_name_rejected(api_as, admin_user, category):
    response = api_as(admin_user).post(
        reverse("category-list"), {"name": category.name.lower()}, format="json"
    )
    assert response.status_code == 400


def test_category_not_found(api_as, admin_user):
    response = api_as(admin_user).get(reverse("category-detail", args=[9999]))
    assert response.status_code == 404


def test_admin_can_update_and_delete_category(api_as, admin_user, category):
    api = api_as(admin_user)
    response = api.patch(reverse("category-detail", args=[category.id]), {"is_active": False}, format="json")
    assert response.status_code == 200
    response = api.delete(reverse("category-detail", args=[category.id]))
    assert response.status_code == 204


def test_anonymous_cannot_list_categories(api):
    assert api.get(reverse("category-list")).status_code == 401
