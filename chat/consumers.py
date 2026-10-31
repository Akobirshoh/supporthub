from datetime import timezone as dt_timezone

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from common.permissions import can_access_ticket
from tickets.models import Ticket

from .models import Message

MAX_MESSAGE_LENGTH = 5000


class TicketChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.ticket_id = int(self.scope["url_route"]["kwargs"]["ticket_id"])
        self.group_name = f"ticket_{self.ticket_id}"
        self.joined = False

        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return

        ticket = await self.get_ticket()
        if ticket is None:
            await self.close(code=4404)
            return
        if not can_access_ticket(user, ticket):
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        self.joined = True
        await self.accept()

    async def disconnect(self, code):
        if getattr(self, "joined", False):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        try:
            content = await self.decode_json(text_data)
        except (TypeError, ValueError):
            await self.send_json({"error": "Noto'g'ri JSON format."})
            return
        await self.receive_json(content)

    async def receive_json(self, content, **kwargs):
        text = content.get("message") if isinstance(content, dict) else None
        if not isinstance(text, str) or not text.strip():
            await self.send_json({"error": "Xabar bo'sh bo'lishi mumkin emas."})
            return
        text = text.strip()
        if len(text) > MAX_MESSAGE_LENGTH:
            await self.send_json({"error": f"Xabar {MAX_MESSAGE_LENGTH} belgidan oshmasligi kerak."})
            return

        payload = await self.save_message(text)
        await self.channel_layer.group_send(
            self.group_name, {"type": "chat.message", "payload": payload}
        )

    async def chat_message(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def get_ticket(self):
        return Ticket.objects.filter(pk=self.ticket_id).first()

    @database_sync_to_async
    def save_message(self, text):
        user = self.scope["user"]
        message = Message.objects.create(ticket_id=self.ticket_id, sender=user, text=text)
        created = message.created_at.astimezone(dt_timezone.utc)
        return {
            "id": message.id,
            "ticket_id": message.ticket_id,
            "sender": user.username,
            "message": message.text,
            "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
