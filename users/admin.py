from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "phone", "is_active", "created_at")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Qo'shimcha", {"fields": ("role", "phone")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Qo'shimcha", {"fields": ("email", "role", "phone")}),
    )
