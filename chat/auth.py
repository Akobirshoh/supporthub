from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken

from users.models import User


@database_sync_to_async
def get_user(token):
    try:
        payload = AccessToken(token)
        return User.objects.get(pk=payload[api_settings.USER_ID_CLAIM], is_active=True)
    except (TokenError, User.DoesNotExist, KeyError, ValueError):
        return AnonymousUser()


def extract_token(scope):
    query = parse_qs(scope.get("query_string", b"").decode())
    if query.get("token"):
        return query["token"][0]
    for name, value in scope.get("headers", []):
        if name == b"authorization":
            parts = value.decode().split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
    return None


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = extract_token(scope)
        scope["user"] = await get_user(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
