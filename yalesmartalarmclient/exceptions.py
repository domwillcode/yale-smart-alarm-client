"""Exceptions for import."""


from typing import Any


class AuthenticationError(Exception):
    def __init__(self, *args: Any) -> None:
        Exception.__init__(self, *args)


class ConnectionError(Exception):
    def __init__(self, *args: Any) -> None:
        Exception.__init__(self, *args)
