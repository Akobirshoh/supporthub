from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import (
    CanSetTicketFields,
    IsAdmin,
    IsAdminOrAssignedOperator,
    IsOperator,
    IsTicketOwner,
)

from .filters import TicketFilter, priority_rank
from .models import Category, Ticket
from .serializers import CategorySerializer, StatisticsSerializer, TicketSerializer
from .stats import get_statistics


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    filterset_class = TicketFilter
    search_fields = ["title", "description"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = Ticket.objects.select_related("client", "operator", "category").annotate(
            priority_rank=priority_rank
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        if self.action != "list":
            return qs

        user = self.request.user
        if user.is_admin:
            return qs
        if user.is_operator:
            return qs.filter(operator=user)
        return qs.filter(client=user)

    def get_permissions(self):
        owner_or_staff = IsTicketOwner | IsAdminOrAssignedOperator
        if self.action == "list":
            classes = [IsAuthenticated]
        elif self.action == "create":
            classes = [IsAuthenticated, CanSetTicketFields]
        elif self.action == "statistics":
            classes = [IsAuthenticated, IsAdmin | IsOperator]
        elif self.action == "destroy":
            classes = [IsAuthenticated, IsAdmin]
        elif self.action in ("update", "partial_update"):
            classes = [IsAuthenticated, CanSetTicketFields, owner_or_staff]
        else:
            classes = [IsAuthenticated, owner_or_staff]
        return [cls() for cls in classes]

    @extend_schema(responses=StatisticsSerializer)
    @action(detail=False, methods=["get"], pagination_class=None)
    def statistics(self, request):
        return Response(get_statistics())
