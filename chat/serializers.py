from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    ticket_id = serializers.IntegerField(read_only=True)
    sender = serializers.CharField(source="sender.username", read_only=True)
    message = serializers.CharField(source="text", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "ticket_id", "sender", "message", "is_read", "created_at")
