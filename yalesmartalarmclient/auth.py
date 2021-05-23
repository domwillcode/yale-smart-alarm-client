#!/usr/bin/env python
import logging
import requests
import backoff
from .exceptions import AuthenticationError, ConnectionError

_LOGGER = logging.getLogger(__name__)


class YaleAuth:
    """
    Handle authentication and creating authorized calls on the yale apis.
    """
    YALE_CODE_RESULT_SUCCESS = '000'

    _HOST = "https://mob.yalehomesystem.co.uk/yapi"
    _ENDPOINT_TOKEN = "/o/token/"
    _ENDPOINT_SERVICES = "/services/"
    _YALE_AUTH_TOKEN = 'VnVWWDZYVjlXSUNzVHJhcUVpdVNCUHBwZ3ZPakxUeXNsRU1LUHBjdTpkd3RPbE15WEtENUJ5ZW1GWHV0am55eGhrc0U3V0ZFY2p0dFcyOXRaSWNuWHlSWHFsWVBEZ1BSZE1xczF4R3VwVTlxa1o4UE5ubGlQanY5Z2hBZFFtMHpsM0h4V3dlS0ZBcGZzakpMcW1GMm1HR1lXRlpad01MRkw3MGR0bmNndQ=='

    _YALE_AUTHENTICATION_REFRESH_TOKEN = 'refresh_token'
    _YALE_AUTHENTICATION_ACCESS_TOKEN = 'access_token'

    _DEFAULT_REQUEST_TIMEOUT = 5
    _MAX_RETRY_SECONDS = 30
    _MAX_TRIES = 5

    def give_up(e):
        """Give up on connecting."""
        try:
            status = e.response.status_code
            #if e.response.status_code == 401:
            #    raise AuthenticationError
        except:
            return False
        raise AuthenticationError

    BACKOFF_RETRY_ON_EXCEPTION_PARAMS = {
        "wait_gen": backoff.expo,
        "exception": requests.exceptions.RequestException,
        "max_tries": _MAX_TRIES,
        "max_time": _MAX_RETRY_SECONDS,
        "giveup": give_up,
    }

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.refresh_token = None
        try:
            self._authorize()
        except AuthenticationError:
            _LOGGER.error("Authentication incorrect")
            raise AuthenticationError
        except:
            _LOGGER.error("Problem connecting to API")
            raise ConnectionError

    @property
    def auth_headers(self):
        return {
            "Authorization": "Bearer " + self.access_token
        }

    @backoff.on_exception(**BACKOFF_RETRY_ON_EXCEPTION_PARAMS)
    def get_authenticated(self, endpoint: str):
        """
        Execute an GET request on an endpoint.
        Args:
            endpoint: parts of an url

        Returns:
            a dictionary with the response.

        """
        url = self._HOST + endpoint
        response = requests.get(url, headers=self.auth_headers, timeout=self._DEFAULT_REQUEST_TIMEOUT)
        if response.status_code != 200:
            self._authorize()
            response = requests.get(url, headers=self.auth_headers, timeout=self._DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()

        return response.json()

    @backoff.on_exception(**BACKOFF_RETRY_ON_EXCEPTION_PARAMS)
    def post_authenticated(self, endpoint: str, params: dict = None):
        if 'panic' in endpoint:
            url = self._HOST[: -5] + endpoint
        else:
            url = self._HOST + endpoint
        response = requests.post(url, headers=self.auth_headers, data=params, timeout=self._DEFAULT_REQUEST_TIMEOUT)
        if response.status_code != 200:
            self._authorize()
            response = requests.post(url, headers=self.auth_headers, data=params, timeout=self._DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()

        if 'panic' in endpoint:
            return True
        else:
            return response.json()

    def _update_services(self):
        data = self.get_authenticated(self._ENDPOINT_SERVICES)
        url = data.get('yapi')
        if url is not None:
            if len(url) > 0:
                _LOGGER.debug("Yale URL updated: " + url)
                if url.endswith('/'):
                    url = url[:-1]
                self._HOST = url
            else:
                _LOGGER.debug("Services URL is empty")
        else:
            _LOGGER.debug("Unable to fetch services")

    @backoff.on_exception(**BACKOFF_RETRY_ON_EXCEPTION_PARAMS)
    def _authorize(self):
        if self.refresh_token:
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }
        else:
            payload = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password
            }
        headers = {
            "Authorization": "Basic " + self._YALE_AUTH_TOKEN,
        }
        url = self._HOST + self._ENDPOINT_TOKEN

        _LOGGER.debug("Attempting authorization")

        response = requests.post(url, headers=headers, data=payload, timeout=self._DEFAULT_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        _LOGGER.debug(f"Authorization response: {data}")
        if data.get("error"):
            if self.refresh_token:
                # Maybe refresh_token has expired, try again with password
                self.refresh_token = None
                return self._authorize()
            _LOGGER.debug("Failed to authenticate with Yale Smart Alarm. Error: %s", data.error)
            raise AuthenticationError("Failed to authenticate with Yale Smart Alarm. Check credentials.")

        _LOGGER.info("Authorization to Yale Alarm API successful.")

        self.refresh_token = data.get(self._YALE_AUTHENTICATION_REFRESH_TOKEN)
        self.access_token = data.get(self._YALE_AUTHENTICATION_ACCESS_TOKEN)
        if self.refresh_token is None or self.access_token is None:
            raise Exception("Failed to authenticate with Yale Smart Alarm. Invalid token.")

        self._update_services()
        return self.access_token, self.refresh_token
