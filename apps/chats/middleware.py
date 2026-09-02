from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_token(token):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import AnonymousUser

    User = get_user_model()

    if not token or not isinstance(token, str):
        return AnonymousUser()

    try:
        access_token = AccessToken(token)

        user_id = access_token.get(
            "user_id",
        )

        if not user_id:
            return AnonymousUser()

        return User.objects.get(
            id=user_id,
            is_active=True,
        )

    except (
        TokenError,
        User.DoesNotExist,
        KeyError,
        TypeError,
        ValueError,
    ):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        scope,
        receive,
        send,
    ):
        query_string = (
            scope.get(
                "query_string",
                b"",
            )
            .decode(
                "utf-8",
            )
        )

        query_params = parse_qs(
            query_string,
        )

        token_values = query_params.get(
            "token",
            [],
        )

        token = (
            token_values[0]
            if token_values
            else None
        )

        scope["user"] = await get_user_from_token(
            token,
        )

        return await super().__call__(
            scope,
            receive,
            send,
        )


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
