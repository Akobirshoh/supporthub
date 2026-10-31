import pytest
from django.urls import reverse

from tickets.models import Ticket, TicketHistory

pytestmark = pytest.mark.django_db


def ticket_payload(category, **extra):
    data = {
        "title": "Internet ishlamayapti",
        "description": "Ulanish uzilib qolyapti",
        "category": category.id,
        "priority": "high",
    }
    data.update(extra)
    return data


def test_client_can_create_ticket(api_as, client_user, category):
    response = api_as(client_user).post(
        reverse("ticket-list"), ticket_payload(category), format="json"
    )
    assert response.status_code == 201
    assert response.data["status"] == "new"
    assert response.data["category_name"] == category.name
    assert Ticket.objects.count() == 1


def test_ticket_client_is_set_automatically(api_as, client_user, other_client, category):
    response = api_as(client_user).post(
        reverse("ticket-list"),
        ticket_payload(category, client=other_client.id),
        format="json",
    )
    assert response.status_code == 201
    assert Ticket.objects.get().client == client_user


def test_client_cannot_set_status_or_operator_on_create(api_as, client_user, operator, category):
    api = api_as(client_user)
    response = api.post(reverse("ticket-list"), ticket_payload(category, status="closed"), format="json")
    assert response.status_code == 403
    response = api.post(reverse("ticket-list"), ticket_payload(category, operator=operator.id), format="json")
    assert response.status_code == 403


def test_client_sees_only_own_tickets(api_as, client_user, other_client, make_ticket):
    make_ticket()
    make_ticket(client=other_client, title="Boshqa mijoz")

    response = api_as(client_user).get(reverse("ticket-list"))
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["title"] == "Internet ishlamayapti"


def test_client_cannot_view_other_clients_ticket(api_as, other_client, make_ticket):
    ticket = make_ticket()
    response = api_as(other_client).get(reverse("ticket-detail", args=[ticket.id]))
    assert response.status_code == 403


def test_operator_sees_only_assigned_tickets(api_as, operator, other_operator, make_ticket):
    mine = make_ticket(operator=operator)
    make_ticket(operator=other_operator, title="Boshqa operatorniki")
    make_ticket(title="Biriktirilmagan")

    api = api_as(operator)
    response = api.get(reverse("ticket-list"))
    assert [t["id"] for t in response.data["results"]] == [mine.id]
    assert api_as(operator).get(reverse("ticket-detail", args=[mine.id])).status_code == 200


def test_operator_cannot_open_unassigned_ticket(api_as, operator, make_ticket):
    ticket = make_ticket()
    response = api_as(operator).get(reverse("ticket-detail", args=[ticket.id]))
    assert response.status_code == 403


def test_admin_sees_all_tickets(api_as, admin_user, other_client, make_ticket):
    make_ticket()
    make_ticket(client=other_client)
    response = api_as(admin_user).get(reverse("ticket-list"))
    assert response.data["count"] == 2


def test_ticket_detail_has_category_and_operator_info(api_as, client_user, operator, make_ticket):
    ticket = make_ticket(operator=operator)
    response = api_as(client_user).get(reverse("ticket-detail", args=[ticket.id]))
    assert response.status_code == 200
    assert response.data["category_name"] == "Texnik muammo"
    assert response.data["operator_detail"]["username"] == "operator1"


def test_client_can_edit_own_ticket_but_not_status(api_as, client_user, make_ticket):
    ticket = make_ticket()
    api = api_as(client_user)
    url = reverse("ticket-detail", args=[ticket.id])

    assert api.patch(url, {"title": "Yangi sarlavha"}, format="json").status_code == 200
    assert api.patch(url, {"status": "resolved"}, format="json").status_code == 403
    assert api.patch(url, {"operator": 1}, format="json").status_code == 403
    ticket.refresh_from_db()
    assert ticket.title == "Yangi sarlavha"
    assert ticket.status == "new"


def test_client_cannot_edit_other_ticket(api_as, other_client, make_ticket):
    ticket = make_ticket()
    response = api_as(other_client).patch(
        reverse("ticket-detail", args=[ticket.id]), {"title": "Hack"}, format="json"
    )
    assert response.status_code == 403


def test_readonly_fields_cannot_be_changed(api_as, client_user, other_client, make_ticket):
    ticket = make_ticket()
    api_as(client_user).patch(
        reverse("ticket-detail", args=[ticket.id]),
        {"client": other_client.id, "created_at": "2020-01-01T00:00:00Z"},
        format="json",
    )
    ticket.refresh_from_db()
    assert ticket.client == client_user
    assert ticket.created_at.year != 2020


def test_operator_changes_status_and_history_is_written(api_as, operator, make_ticket):
    ticket = make_ticket(operator=operator)
    api = api_as(operator)
    url = reverse("ticket-detail", args=[ticket.id])

    assert api.patch(url, {"status": "in_progress"}, format="json").status_code == 200
    response = api.patch(url, {"status": "resolved"}, format="json")
    assert response.status_code == 200
    assert response.data["resolved_at"] is not None
    assert TicketHistory.objects.filter(ticket=ticket).count() == 2

    assert api.patch(url, {"title": "Boshqa"}, format="json").status_code == 403


def test_operator_cannot_manage_foreign_ticket(api_as, operator, other_operator, make_ticket):
    ticket = make_ticket(operator=other_operator)
    response = api_as(operator).patch(
        reverse("ticket-detail", args=[ticket.id]), {"status": "closed"}, format="json"
    )
    assert response.status_code == 403


def test_admin_assigns_operator(api_as, admin_user, operator, client_user, make_ticket):
    ticket = make_ticket()
    url = reverse("ticket-detail", args=[ticket.id])
    api = api_as(admin_user)

    assert api.patch(url, {"operator": operator.id}, format="json").status_code == 200
    assert api.patch(url, {"operator": client_user.id}, format="json").status_code == 400


def test_only_admin_can_delete(api_as, client_user, admin_user, make_ticket):
    ticket = make_ticket()
    url = reverse("ticket-detail", args=[ticket.id])
    assert api_as(client_user).delete(url).status_code == 403
    assert api_as(admin_user).delete(url).status_code == 204


def test_tickets_require_authentication(api):
    assert api.get(reverse("ticket-list")).status_code == 401
