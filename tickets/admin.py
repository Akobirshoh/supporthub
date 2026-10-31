from django.contrib import admin

from .models import Category, Ticket, TicketHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "client", "operator", "category", "status", "priority", "created_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("title", "description", "client__username")
    raw_id_fields = ("client", "operator")


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ("ticket", "changed_by", "old_status", "new_status", "created_at")
    list_filter = ("new_status",)
