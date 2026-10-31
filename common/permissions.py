from rest_framework.permissions import SAFE_METHODS, BasePermission


def can_access_ticket(user, ticket):
    if not user or not user.is_authenticated:
        return False
    if user.is_admin:
        return True
    if ticket.client_id == user.id:
        return True
    return user.is_operator and ticket.operator_id == user.id


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)


class IsOperator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_operator)


class IsTicketOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_authenticated and obj.client_id == request.user.id)


class IsAdminOrAssignedOperator(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        return user.is_operator and obj.operator_id == user.id


class CanSetTicketFields(BasePermission):
    message = "Bu maydonlarni o'zgartirishga ruxsatingiz yo'q."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS or request.method == "DELETE":
            return True
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_admin:
            return True

        sent = set(request.data.keys()) if hasattr(request.data, "keys") else set()
        if view.action == "create":
            blocked = {"status", "operator"}
        elif user.is_operator:
            blocked = {"title", "description", "category", "operator"}
        else:
            blocked = {"status", "operator"}
        return not (sent & blocked)
