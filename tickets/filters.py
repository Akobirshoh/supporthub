import django_filters
from django.db.models import Case, IntegerField, Value, When

from .models import Ticket

PRIORITY_ORDER = ["low", "medium", "high", "urgent"]

priority_rank = Case(
    *[When(priority=name, then=Value(index)) for index, name in enumerate(PRIORITY_ORDER, start=1)],
    default=Value(0),
    output_field=IntegerField(),
)


class TicketFilter(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("priority_rank", "priority"),
        )
    )

    class Meta:
        model = Ticket
        fields = ["status", "priority", "category", "operator"]
