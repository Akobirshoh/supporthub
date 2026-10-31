import pytest
from django.urls import reverse

from users.models import User

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


def test_register_success(api):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "phone": "+998901234567",
        "password": PASSWORD,
    }
    response = api.post(reverse("register"), payload, format="json")

    assert response.status_code == 201
    assert "password" not in response.data
    user = User.objects.get(username="newuser")
    assert user.role == "client"
    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)


def test_register_duplicate_email(api, client_user):
    payload = {"username": "another", "email": client_user.email, "password": PASSWORD}
    response = api.post(reverse("register"), payload, format="json")
    assert response.status_code == 400
    assert "email" in response.data


def test_login_returns_tokens(api, client_user):
    response = api.post(
        reverse("login"), {"username": "ali", "password": PASSWORD}, format="json"
    )
    assert response.status_code == 200
    assert "access" in response.data and "refresh" in response.data


def test_login_wrong_password(api, client_user):
    response = api.post(
        reverse("login"), {"username": "ali", "password": "wrong-password"}, format="json"
    )
    assert response.status_code == 401
    assert "access" not in response.data


def test_profile_requires_token(api):
    response = api.get(reverse("profile"))
    assert response.status_code == 401


def test_profile_with_token_and_patch(api, client_user):
    tokens = api.post(
        reverse("login"), {"username": "ali", "password": PASSWORD}, format="json"
    ).data
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    response = api.get(reverse("profile"))
    assert response.status_code == 200
    assert response.data["username"] == "ali"

    response = api.patch(reverse("profile"), {"phone": "+998900000000", "role": "admin"}, format="json")
    assert response.status_code == 200
    client_user.refresh_from_db()
    assert client_user.phone == "+998900000000"
    assert client_user.role == "client"


def test_token_refresh(api, client_user):
    tokens = api.post(
        reverse("login"), {"username": "ali", "password": PASSWORD}, format="json"
    ).data
    response = api.post(reverse("token-refresh"), {"refresh": tokens["refresh"]}, format="json")
    assert response.status_code == 200
    assert "access" in response.data
