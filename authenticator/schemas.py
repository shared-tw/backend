from typing import Optional

from ninja import Schema


class JWTTokenCreation(Schema):
    username: str
    password: str


class JWTToken(Schema):
    access: str
    refresh: Optional[str]


class JWTRefreshToken(Schema):
    refresh: str
