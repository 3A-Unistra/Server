import random
import traceback
from typing import Optional
from urllib.parse import parse_qs
from uuid import UUID

import jwt
import names
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from jwt import InvalidTokenError

from server.game_handler.models import User
from django.conf import settings


def is_valid_uuid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.

     Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

     Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

     Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """

    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


class AuthMiddleware:
    """
    Middleware for WebSocket connections.
    Check jwt's token validity before connection.
    OR
    Accept connection with game_token (for local server)

    -> key: private key for jwt encryption
    """

    def __init__(self, app):
        self.app = app
        self.offline = getattr(settings, "SERVER_OFFLINE", True)
        self.key = getattr(settings, "JWT_KEY", None)

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            # get token from url
            query = scope["query_string"].decode("utf8")
            token = parse_qs(query).get('token', None)

            print("middleware: get %s" % query)

            if (jwt_token_list := token) is not None:

                # could be an uuid
                jwt_token = jwt_token_list[0]

                # check if token is an uuid
                if self.offline:
                    if not is_valid_uuid(jwt_token):
                        print("Middleware: user uuid not valid")
                        scope['user'] = None
                        return None
                    else:
                        print("Middleware: user uuid valid")
                        token = jwt_token
                else:
                    # decode jwt and get jti
                    encoded = jwt.decode(jwt_token, self.key,
                                         algorithms=["HS256"])
                    token = encoded.get('jti')

                # get user from db
                scope['user'] = await self.get_user(token)
            else:
                scope['user'] = None
                return None
        except (InvalidTokenError, KeyError):
            traceback.print_exc()
            scope['user'] = None
            return None
        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        try:
            return User.objects.get(id=token)
        except User.DoesNotExist:

            # If server offline, and user not found, create new user
            if self.offline:
                random_name = names.get_first_name()

                user = User()
                user.id = token
                user.login = '%s%d'.lower() % (
                    random_name, random.randint(0, 100))
                user.name = names.get_first_name()
                user.piece = 1
                user.email = 'test@test.fr'
                user.password = token
                user.avatar = ""
                user.save()

                print("Creating new user=%s" % token)

                return user

            return None
