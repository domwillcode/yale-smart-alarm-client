"""Module for handling authentication against the Yale Smart API."""
import logging
from typing import Any, Dict, Literal, Optional, Tuple, Union, cast

import backoff
import requests

from .exceptions import AuthenticationError

_LOGGER = logging.getLogger(__name__)


class YaleAuth:
    """Handle authentication and creating authorized calls on the yale apis."""

    YALE_CODE_RESULT_SUCCESS = "000"

    _HOST = "https://mob.yalehomesystem.co.uk/yapi"
    _ENDPOINT_TOKEN = "/o/token/"
    _ENDPOINT_SERVICES = "/services/"
    _YALE_AUTH_TOKEN = "VnVWWDZYVjlXSUNzVHJhcUVpdVNCUHBwZ3ZPakxUeXNsRU1LUHBjdTpkd3RPbE15WEtENUJ5ZW1GWHV0am55eGhrc0U3V0ZFY2p0dFcyOXRaSWNuWHlSWHFsWVBEZ1BSZE1xczF4R3VwVTlxa1o4UE5ubGlQanY5Z2hBZFFtMHpsM0h4V3dlS0ZBcGZzakpMcW1GMm1HR1lXRlpad01MRkw3MGR0bmNndQ=="

    _YALE_AUTHENTICATION_REFRESH_TOKEN = "refresh_token"
    _YALE_AUTHENTICATION_ACCESS_TOKEN = "access_token"

    _DEFAULT_REQUEST_TIMEOUT = 5
    _MAX_RETRY_SECONDS = 30
    _MAX_TRIES = 5

    @staticmethod
    def _give_up(e: requests.exceptions.RequestException) -> bool:
        """Give up on connecting."""
        try:
            status = e.response.status_code
            # if e.response.status_code == 401:
            #    raise AuthenticationError
        except requests.RequestException:
            return False
        raise AuthenticationError

    BACKOFF_RETRY_ON_EXCEPTION_PARAMS = {
        "wait_gen": backoff.expo,
        "exception": requests.exceptions.RequestException,
        "max_tries": _MAX_TRIES,
        "max_time": _MAX_RETRY_SECONDS,
        "giveup": _give_up,
    }

    def __init__(self, username: str, password: str) -> None:
        """Initialize Authentication module."""
        self.username = username
        self.password = password
        self.refresh_token: Optional[str] = None
        self.access_token: Optional[str] = None
        try:
            self._authorize()
        except AuthenticationError as e:
            _LOGGER.error("Authentication incorrect")
            raise e
        except requests.RequestException as e:
            _LOGGER.error("Problem connecting to API")
            raise e

    @property
    def auth_headers(self) -> Dict[str, str]:
        """Return authentication headers."""
        return {"Authorization": "Bearer " + self.access_token}

    @backoff.on_exception(**BACKOFF_RETRY_ON_EXCEPTION_PARAMS)
    def get_authenticated(self, endpoint: str) -> Dict[str, Any]:
        """Execute an GET request on an endpoint.

        Args:
            endpoint: parts of an url.

        Returns:
            a dictionary with the response.

        """
        url = self._HOST + endpoint
        response = requests.get(
            url, headers=self.auth_headers, timeout=self._DEFAULT_REQUEST_TIMEOUT
        )
        if response.status_code != 200:
            self._authorize()
            response = requests.get(
                url, headers=self.auth_headers, timeout=self._DEFAULT_REQUEST_TIMEOUT
            )
            response.raise_for_status()

        return cast(Dict[str, Any], response.json())

    @backoff.on_exception(**BACKOFF_RETRY_ON_EXCEPTION_PARAMS)
    def post_authenticated(
        self, endpoint: str, params: Optional[Dict[Any, Any]] = None
    ) -> Union[Literal[True], Dict[str, Any]]:
        """Execute a POST request on an endpoint.

        Args:
            endpoint: URL endpoint to connect to.

        Returns:
            A dictionary with the response.

        """
        if "panic" in endpoint:
            url = self._HOST[:-5] + endpoint
        else:
            url = self._HOST + endpoint
        response: requests.Response = requests.post(
            url,
            headers=self.auth_headers,
            data=params,
            timeout=self._DEFAULT_REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            self._authorize()
            response = requests.post(
                url,
                headers=self.auth_headers,
                data=params,
                timeout=self._DEFAULT_REQUEST_TIMEOUT,
            )
            response.raise_for_status()

        if "panic" in endpoint:
            return True
        else:
            return cast(Dict[str, Any], response.json())

    def _update_services(self) -> None:
        data = self.get_authenticated(self._ENDPOINT_SERVICES)
        url = data.get("yapi")
        if url is not None:
            if len(url) > 0:
                _LOGGER.debug("Yale URL updated: " + url)
                if url.endswith("/"):
                    url = url[:-1]
                self._HOST = url
            else:
                _LOGGER.debug("Services URL is empty")
        else:
            _LOGGER.debug("Unable to fetch services")

    @backoff.on_exception(**BACKOFF_RETRY_ON_EXCEPTION_PARAMS)
    def _authorize(self) -> Tuple[str, str]:
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
            "Authorization": "Basic " + self._YALE_AUTH_TOKEN,
        }
        url = self._HOST + self._ENDPOINT_TOKEN

        _LOGGER.debug("Attempting authorization")

        response: requests.Response = requests.post(
            url, headers=headers, data=payload, timeout=self._DEFAULT_REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        _LOGGER.debug(f"Authorization response: {data}")
        if data.get("error"):
            if self.refresh_token:
                # Maybe refresh_token has expired, try again with password
                self.refresh_token = None
                return self._authorize()
            _LOGGER.debug(
                "Failed to authenticate with Yale Smart Alarm. Error: %s", data.error
            )
            raise AuthenticationError(
                "Failed to authenticate with Yale Smart Alarm. Check credentials."
            )

        _LOGGER.info("Authorization to Yale Alarm API successful.")

        self.refresh_token = data.get(self._YALE_AUTHENTICATION_REFRESH_TOKEN)
        self.access_token = data.get(self._YALE_AUTHENTICATION_ACCESS_TOKEN)
        if self.refresh_token is None or self.access_token is None:
            raise AuthenticationError(
                "Failed to authenticate with Yale Smart Alarm. Invalid token."
            )

        self._update_services()
        return self.access_token, self.refresh_token
