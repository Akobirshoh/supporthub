import logging

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_response_time_header(api_as, client_user):
    response = api_as(client_user).get(reverse("ticket-list"))
    assert "X-Response-Time" in response
    assert response["X-Response-Time"].endswith("s")


def test_request_is_logged(api_as, client_user, caplog):
    with caplog.at_level(logging.INFO, logger="supporthub.requests"):
        api_as(client_user).get(reverse("ticket-list"))
    text = caplog.text
    assert f"User={client_user.pk}" in text
    assert "Method=GET" in text
    assert "Path=/api/tickets/" in text
    assert "Status=200" in text
    assert "Duration=" in text


def test_admin_and_static_paths_are_not_logged(api, caplog):
    with caplog.at_level(logging.INFO, logger="supporthub.requests"):
        api.get("/admin/login/")
        api.get("/static/nothing.css")
    assert "Path=/admin/" not in caplog.text
    assert "Path=/static/" not in caplog.text


def test_unexpected_error_is_logged(admin_user, caplog):
    from unittest import mock

    from django.test import Client
    from rest_framework_simplejwt.tokens import AccessToken

    token = str(AccessToken.for_user(admin_user))
    client = Client(raise_request_exception=False)
    with caplog.at_level(logging.ERROR, logger="supporthub.requests"):
        with mock.patch("tickets.views.get_statistics", side_effect=RuntimeError("buzildi")):
            response = client.get("/api/tickets/statistics/", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 500
    assert "Kutilmagan xato" in caplog.text
    assert "buzildi" in caplog.text
    assert "X-Response-Time" in response
