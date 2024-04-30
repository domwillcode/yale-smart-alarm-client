"""Exceptions handling for Yale Smart Alarm."""


class AuthenticationError(Exception):
    """Exception to indicate an issue with the authentication against the Yale Smart API."""


class UnknownError(Exception):
    """Exception to indicate an unknown issue against the Yale Smart API."""
