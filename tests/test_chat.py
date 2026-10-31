import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken

from chat.models import Message
from supporthub.asgi import application

pytestmark = pytest.mark.django_db(transaction=True)


def token_for(user):
    return str(AccessToken.for_user(user))


def connect(ticket_id, user=None):
    path = f"/ws/tickets/{ticket_id}/"
    if user is not None:
        path += f"?token={token_for(user)}"
    return WebsocketCommunicator(application, path)


async def test_anonymous_user_cannot_connect(make_ticket):
    ticket = await database_sync_to_async(make_ticket)()
    communicator = connect(ticket.id)
    connected, _ = await communicator.connect()
    assert connected is False


async def test_invalid_token_cannot_connect(make_ticket):
    ticket = await database_sync_to_async(make_ticket)()
    communicator = WebsocketCommunicator(application, f"/ws/tickets/{ticket.id}/?token=abc")
    connected, _ = await communicator.connect()
    assert connected is False


async def test_message_is_saved_to_database(client_user, make_ticket):
    ticket = await database_sync_to_async(make_ticket)()
    communicator = connect(ticket.id, client_user)
    connected, _ = await communicator.connect()
    assert connected is True

    await communicator.send_json_to({"message": "Muammo hali ham hal bo'lmadi."})
    data = await communicator.receive_json_from()

    assert data["ticket_id"] == ticket.id
    assert data["sender"] == "ali"
    assert data["message"] == "Muammo hali ham hal bo'lmadi."
    assert data["created_at"].endswith("Z")

    saved = await database_sync_to_async(Message.objects.get)(pk=data["id"])
    assert saved.text == "Muammo hali ham hal bo'lmadi."
    assert saved.sender_id == client_user.id
    await communicator.disconnect()


async def test_message_reaches_all_participants(client_user, operator, make_ticket):
    ticket = await database_sync_to_async(make_ticket)(operator=operator)
    first = connect(ticket.id, client_user)
    second = connect(ticket.id, operator)
    assert (await first.connect())[0] and (await second.connect())[0]

    await first.send_json_to({"message": "Salom"})
    assert (await first.receive_json_from())["message"] == "Salom"
    received = await second.receive_json_from()
    assert received["message"] == "Salom"
    assert received["sender"] == "ali"

    await second.send_json_to({"message": "Yordam beraman"})
    assert (await first.receive_json_from())["sender"] == "operator1"
    await first.disconnect()
    await second.disconnect()


async def test_empty_message_is_rejected(client_user, make_ticket):
    ticket = await database_sync_to_async(make_ticket)()
    communicator = connect(ticket.id, client_user)
    await communicator.connect()

    await communicator.send_json_to({"message": "   "})
    response = await communicator.receive_json_from()
    assert "error" in response
    assert await database_sync_to_async(Message.objects.count)() == 0
    await communicator.disconnect()


async def test_stranger_cannot_connect(other_client, make_ticket):
    ticket = await database_sync_to_async(make_ticket)()
    connected, _ = await connect(ticket.id, other_client).connect()
    assert connected is False


async def test_unassigned_operator_cannot_connect(operator, make_ticket):
    ticket = await database_sync_to_async(make_ticket)()
    connected, _ = await connect(ticket.id, operator).connect()
    assert connected is False


async def test_admin_can_connect(admin_user, make_ticket):
    ticket = await database_sync_to_async(make_ticket)()
    communicator = connect(ticket.id, admin_user)
    connected, _ = await communicator.connect()
    assert connected is True
    await communicator.disconnect()


async def test_nonexistent_ticket_is_rejected(client_user):
    connected, _ = await connect(99999, client_user).connect()
    assert connected is False


def test_message_history_endpoint(api_as, client_user, other_client, make_ticket):
    ticket = make_ticket()
    for index in range(3):
        Message.objects.create(ticket=ticket, sender=client_user, text=f"Xabar {index}")

    response = api_as(client_user).get(reverse("ticket-messages", args=[ticket.id]), {"page_size": 2})
    assert response.status_code == 200
    assert response.data["count"] == 3
    assert response.data["total_pages"] == 2
    assert response.data["results"][0]["message"] == "Xabar 0"
    assert api_as(other_client).get(reverse("ticket-messages", args=[ticket.id])).status_code == 403


def test_mark_messages_as_read(api_as, client_user, operator, make_ticket):
    ticket = make_ticket(operator=operator)
    Message.objects.create(ticket=ticket, sender=client_user, text="Salom")
    response = api_as(operator).post(reverse("ticket-messages-read", args=[ticket.id]))
    assert response.data["updated"] == 1
    assert Message.objects.get().is_read is True
