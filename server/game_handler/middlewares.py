import traceback
from urllib.parse import parse_qs

import jwt
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
                encoded = jwt.decode(jwt_token, "todefineinenv",
                                     algorithms=["HS256"])

                # user = await self.get_logged_in_user(token=validated_token)
                scope['user'] = None  # user
            else:
                scope['user'] = AnonymousUser()
                return None
        except (TokenExc, KeyError):
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

