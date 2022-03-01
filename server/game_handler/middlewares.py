import traceback
from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from jwt import InvalidTokenError

from server.game_handler.models import User
from django.conf import settings


class JWTAuthMiddleware:
    """
    Middleware for WebSocket connections.
    Check jwt's token validity before connection.

    -> key: private key for jwt encryption
    """

    def __init__(self, app):
        self.app = app
        self.key = getattr(settings, "JWT_KEY", None)

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            # get token from url
            query = scope["query_string"].decode("utf8")
            token = parse_qs(query).get('token', None)

            if (jwt_token_list := token) is not None:
                jwt_token = jwt_token_list[0]
                # decode jwt and get jti
                encoded = jwt.decode(jwt_token, self.key,
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
