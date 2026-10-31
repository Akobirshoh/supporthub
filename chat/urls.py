from django.urls import path

from .views import MessageListView, MessageReadView

urlpatterns = [
    path("tickets/<int:ticket_id>/messages/", MessageListView.as_view(), name="ticket-messages"),
    path("tickets/<int:ticket_id>/messages/read/", MessageReadView.as_view(), name="ticket-messages-read"),
]
