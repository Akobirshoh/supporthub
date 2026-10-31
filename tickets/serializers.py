from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from users.models import Role, User
from users.serializers import UserShortSerializer

from .models import Category, Ticket, TicketHistory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "description", "is_active", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_name(self, value):
        value = value.strip()
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bunday nomli kategoriya allaqachon mavjud.")
        return value


class TicketSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True)
    )
    operator = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=Role.OPERATOR, is_active=True),
        required=False,
        allow_null=True,
    )
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    operator_detail = UserShortSerializer(source="operator", read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "title",
            "description",
            "client",
            "category",
            "category_name",
            "operator",
            "operator_detail",
            "status",
            "priority",
            "created_at",
            "updated_at",
            "resolved_at",
        )
        read_only_fields = ("id", "client", "created_at", "updated_at", "resolved_at")

    def create(self, validated_data):
        validated_data["client"] = self.context["request"].user
        validated_data["status"] = Ticket.Status.NEW
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", old_status)
        changed = new_status != old_status

        if changed:
            if new_status in (Ticket.Status.RESOLVED, Ticket.Status.CLOSED):
                validated_data["resolved_at"] = instance.resolved_at or timezone.now()
            else:
                validated_data["resolved_at"] = None

        ticket = super().update(instance, validated_data)

        if changed:
            TicketHistory.objects.create(
                ticket=ticket,
                changed_by=self.context["request"].user,
                old_status=old_status,
                new_status=new_status,
            )
        return ticket


class StatisticsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    new = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    resolved = serializers.IntegerField()
    closed = serializers.IntegerField()
    urgent = serializers.IntegerField()
