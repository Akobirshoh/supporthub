from django.conf import settings
from django.db import models


class Message(models.Model):
    ticket = models.ForeignKey("tickets.Ticket", on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"#{self.ticket_id} {self.sender_id}: {self.text[:30]}"
