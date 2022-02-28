import traceback
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser, User
from django.db import close_old_connections


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            if (jwt_token_list := parse_qs(scope["query_string"].decode("utf8")).get('token', None)) is not None:
                jwt_token = jwt_token_list[0]
                validated_token = JWTTokenUserAuthentication().get_validated_token(
                    raw_token=jwt_token
                )
                user = await self.get_logged_in_user(token=validated_token)
                scope['user'] = user
            else:
                scope['user'] = AnonymousUser()
                return None
        except (InvalidToken, KeyError):
            traceback.print_exc()
            scope['user'] = AnonymousUser()
            return None
        return await self.app(scope, receive, send)

    async def get_logged_in_user(self, token):
        user = await self.get_user(token)
        return user

    @database_sync_to_async
    def get_user(self, token):
        try:
            return JWTTokenUserAuthentication().get_user(validated_token=token)
        except User.DoesNotExist:
            return AnonymousUser()

