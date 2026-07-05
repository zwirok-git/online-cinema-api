from datetime import datetime, timezone

import jwt

from core.config import settings
from exceptions.auth import TokenExpired, TokenInvalid


class JWTService:
    def __init__(self) -> None:
        self._secret = settings.TOKEN_SECRET_KEY
        self._algorithm = settings.TOKEN_ALGORITHM
        self._access_token_expire = settings.ACCESS_TOKEN_EXPIRE
        self._refresh_token_expire = settings.REFRESH_TOKEN_EXPIRE

    def create_access_token(
        self,
        data: dict,
    ) -> str:
        now = datetime.now(timezone.utc)
        to_encode = {
            "sub": str(data["user_id"]),
            "type": "access",
            "iat": now,
            "exp": now + self._access_token_expire,
        }
        encoded_jwt = jwt.encode(
            to_encode, self._secret, algorithm=self._algorithm
        )
        return encoded_jwt

    def create_refresh_token(
        self,
        data: dict,
    ):
        now = datetime.now(timezone.utc)
        to_encode = {
            "sub": str(data["user_id"]),
            "type": "refresh",
            "iat": now,
            "exp": now + self._refresh_token_expire,
        }
        encoded_jwt = jwt.encode(
            to_encode, self._secret, algorithm=self._algorithm
        )
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        try:
            data = jwt.decode(
                token, self._secret, algorithms=[self._algorithm]
            )
            return data
        except jwt.ExpiredSignatureError:
            raise TokenExpired("This token has expired.") from None
        except jwt.PyJWTError:
            raise TokenInvalid("This token is invalid.") from None
