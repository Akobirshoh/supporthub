from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrAssignedOperator, IsTicketOwner
from tickets.models import Ticket

from .models import Message
from .serializers import MessageSerializer


class TicketMessagesMixin:
    permission_classes = [IsAuthenticated, IsTicketOwner | IsAdminOrAssignedOperator]

    def get_ticket(self):
        ticket = get_object_or_404(Ticket, pk=self.kwargs["ticket_id"])
        self.check_object_permissions(self.request, ticket)
        return ticket


class MessageListView(TicketMessagesMixin, generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Message.objects.none()
        ticket = self.get_ticket()
        return Message.objects.filter(ticket=ticket).select_related("sender")


class MessageReadView(TicketMessagesMixin, APIView):
    @extend_schema(
        request=None,
        responses=inline_serializer("MessageReadResult", {"updated": serializers.IntegerField()}),
    )
    def post(self, request, ticket_id):
        ticket = self.get_ticket()
        updated = (
            Message.objects.filter(ticket=ticket, is_read=False)
            .exclude(sender=request.user)
            .update(is_read=True)
        )
        return Response({"updated": updated}, status=status.HTTP_200_OK)
