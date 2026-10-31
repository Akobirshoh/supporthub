import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from tickets.models import Category, Ticket
from users.models import Role, User

PASSWORD = "Str0ng-Pass-123"


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def make_user(username, role=Role.CLIENT):
    return User.objects.create_user(
        username=username, email=f"{username}@example.com", password=PASSWORD, role=role
    )


@pytest.fixture
def client_user(db):
    return make_user("ali")


@pytest.fixture
def other_client(db):
    return make_user("vali")


@pytest.fixture
def operator(db):
    return make_user("operator1", Role.OPERATOR)


@pytest.fixture
def other_operator(db):
    return make_user("operator2", Role.OPERATOR)


@pytest.fixture
def admin_user(db):
    return make_user("admin1", Role.ADMIN)


@pytest.fixture
def category(db):
    return Category.objects.create(name="Texnik muammo")


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def api_as():
    def _login(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _login


@pytest.fixture
def make_ticket(client_user, category):
    def _make(**kwargs):
        data = {
            "title": "Internet ishlamayapti",
            "description": "Ulanish uzilib qolyapti",
            "client": client_user,
            "category": category,
        }
        data.update(kwargs)
        return Ticket.objects.create(**data)

    return _make
