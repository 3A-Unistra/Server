import traceback
from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from jwt import InvalidTokenError

from server.game_handler.models import User

"""
Middleware for WebSocket connections.
Check jwt's token validity before connection.
"""


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            # get token from url
            if (jwt_token_list := parse_qs(scope["query_string"].decode("utf8")).get('token', None)) is not None:
                jwt_token = jwt_token_list[0]
                # decode jwt and get jti
                encoded = jwt.decode(jwt_token, "todefineinenv",
                                     algorithms=["HS256"])
                # get user from db
                user = await self.get_user(token=encoded.get('jti'))
                scope['user'] = user
            else:
                scope['user'] = AnonymousUser()
                return None
        except (InvalidTokenError, KeyError):
            traceback.print_exc()
            scope['user'] = AnonymousUser()
            return None
        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        try:
            return User.objects.get(id=token)
        except User.DoesNotExist:
            return AnonymousUser()
