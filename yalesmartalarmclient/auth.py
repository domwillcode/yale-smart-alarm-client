"""Module for handling authentication against the Yale Smart API."""
from __future__ import annotations

import logging
from typing import Any, cast

import requests
from requests.exceptions import (  # pylint: disable=redefined-builtin
    HTTPError,
    ConnectionError,
    Timeout,
    RequestException,
)

from .exceptions import AuthenticationError, UnknownError
from .const import (
    HOST,
    ENDPOINT_TOKEN,
    ENDPOINT_SERVICES,
    YALE_AUTH_TOKEN,
    YALE_AUTHENTICATION_REFRESH_TOKEN,
    YALE_AUTHENTICATION_ACCESS_TOKEN,
    DEFAULT_REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class YaleAuth:
    """Handle authentication and creating authorized calls on the yale apis."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize Authentication module."""
        self._host = HOST
        self.username = username
        self.password = password
        self.refresh_token: str | None = None
        self.access_token: str | None = None
        self._authorize()

    @property
    def auth_headers(self) -> dict[str, str]:
        """Return authentication headers."""
        if self.access_token:
            return {"Authorization": "Bearer " + self.access_token}
        return {"Authorization": "Bearer "}

    def get_authenticated(self, endpoint: str) -> dict[str, Any]:
        """Execute an GET request on an endpoint.

        Args:
            endpoint: parts of an url.

        Returns:
            a dictionary with the response.

        """
        url = self._host + endpoint

        try:
            response = requests.get(
                url, headers=self.auth_headers, timeout=DEFAULT_REQUEST_TIMEOUT
            )
            response.raise_for_status()
        except HTTPError as error:
            _LOGGER.debug("Http Error: %s", error)
            if response.status_code in [401, 403]:
                self.refresh_token = None
                self.access_token = None
                self._authorize()
                self.get_authenticated(endpoint)
            raise ConnectionError(f"Connection error {error}") from error
        except ConnectionError as error:
            _LOGGER.debug("Connection Error: %s", error)
            raise ConnectionError(f"Connection error {error}") from error
        except Timeout as error:
            _LOGGER.debug("Timeout Error: %s", error)
            raise TimeoutError(f"Timeout {error}") from error
        except RequestException as error:
            _LOGGER.debug("Requests Error: %s", error)
            raise UnknownError(f"Requests error {error}") from error
        except Exception as error:
            _LOGGER.debug("Unknown Error: %s", error)
            raise UnknownError(f"Unknown error {error}") from error

        return cast(dict[str, Any], response.json())

    def post_authenticated(
        self, endpoint: str, params: dict[Any, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a POST request on an endpoint.

        Args:
            endpoint: URL endpoint to connect to.

        Returns:
            A dictionary with the response.

        """
        if "panic" in endpoint:
            url = self._host[:-5] + endpoint
        else:
            url = self._host + endpoint

        try:
            response = requests.post(
                url,
                headers=self.auth_headers,
                data=params,
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except HTTPError as error:
            _LOGGER.debug("Http Error: %s", error)
            if response.status_code in [401, 403]:
                self.refresh_token = None
                self.access_token = None
                self._authorize()
                self.post_authenticated(endpoint, params)
            raise ConnectionError(f"Connection error {error}") from error
        except ConnectionError as error:
            _LOGGER.debug("Connection Error: %s", error)
            raise ConnectionError(f"Connection error {error}") from error
        except Timeout as error:
            _LOGGER.debug("Timeout Error: %s", error)
            raise TimeoutError(f"Timeout {error}") from error
        except RequestException as error:
            _LOGGER.debug("Requests Error: %s", error)
            raise UnknownError(f"Requests error {error}") from error
        except Exception as error:
            _LOGGER.debug("Unknown Error: %s", error)
            raise UnknownError(f"Unknown error {error}") from error

        if "panic" in endpoint:
            return {"panic": "triggered"}
        return cast(dict[str, Any], response.json())

    def _update_services(self) -> None:
        data = self.get_authenticated(ENDPOINT_SERVICES)
        url = data.get("yapi")
        if url is not None:
            if len(url) > 0:
                _LOGGER.debug("Yale URL updated: %s", url)
                if url.endswith("/"):
                    url = url[:-1]
                self._host = url
            else:
                _LOGGER.debug("Services URL is empty")
        else:
            _LOGGER.debug("Unable to fetch services")

    def _authorize(self) -> tuple[str, str]:
        if self.refresh_token:
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            }
        else:
            payload = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            }
        headers = {
            "Authorization": "Basic " + YALE_AUTH_TOKEN,
        }
        url = self._host + ENDPOINT_TOKEN

        _LOGGER.debug("Attempting authorization")

        try:
            response = requests.post(
                url, headers=headers, data=payload, timeout=DEFAULT_REQUEST_TIMEOUT
            )
            response.raise_for_status()
        except HTTPError as error:
            _LOGGER.debug("Http Error: %s", error)
            if response.status_code in [401, 403]:
                raise AuthenticationError(f"Failed to authenticate {error}") from error
            raise ConnectionError(f"Connection error {error}") from error
        except ConnectionError as error:
            _LOGGER.debug("Connection Error: %s", error)
            raise ConnectionError(f"Connection error {error}") from error
        except Timeout as error:
            _LOGGER.debug("Timeout Error: %s", error)
            raise TimeoutError(f"Timeout {error}") from error
        except RequestException as error:
            _LOGGER.debug("Requests Error: %s", error)
            raise UnknownError(f"Requests error {error}") from error
        except Exception as error:
            _LOGGER.debug("Unknown Error: %s", error)
            raise UnknownError(f"Unknown error {error}") from error

        data = response.json()
        _LOGGER.debug("Authorization response: %s", data)
        _LOGGER.info("Authorization to Yale Alarm API successful")

        self.refresh_token = data.get(YALE_AUTHENTICATION_REFRESH_TOKEN)
        self.access_token = data.get(YALE_AUTHENTICATION_ACCESS_TOKEN)
        if self.refresh_token is None or self.access_token is None:
            raise AuthenticationError(
                "Failed to authenticate with Yale Smart Alarm. Invalid token."
            )

        self._update_services()
        return self.access_token, self.refresh_token
