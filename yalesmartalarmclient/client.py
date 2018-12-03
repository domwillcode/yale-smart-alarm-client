#!/usr/bin/env python
"""Yale Smart Alarm client is a python client for interacting with the Yale Smart Alarm System API.

See https://github.com/domwillcode/yale-smart-alarm-client for more information.
"""

import logging
import requests

_LOGGER = logging.getLogger(__name__)

YALE_STATE_ARM_FULL = "arm"
YALE_STATE_ARM_PARTIAL = "home"
YALE_STATE_DISARM = "disarm"


class AuthenticationError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class YaleSmartAlarmClient:
    YALE_CODE_AUTHENTICATION_ERROR = '999'
    YALE_CODE_RESULT_SUCCESS = '000'

    YALE_AUTHENTICATION_TOKEN_NAME = 'PHPSESSID'

    _HOST= "https://mob.yalehomesystem.co.uk:6013/yapi"
    _ENDPOINT_TOKEN = "/o/token/"
    _ENDPOINT_GET_MODE = "/api/panel/mode/"
    _ENDPOINT_SET_MODE = "/api/panel/mode/"

    _YALE_AUTH_TOKEN = 'VnVWWDZYVjlXSUNzVHJhcUVpdVNCUHBwZ3ZPakxUeXNsRU1LUHBjdTpkd3RPbE15WEtENUJ5ZW1GWHV0am55eGhrc0U3V0ZFY2p0dFcyOXRaSWNuWHlSWHFsWVBEZ1BSZE1xczF4R3VwVTlxa1o4UE5ubGlQanY5Z2hBZFFtMHpsM0h4V3dlS0ZBcGZzakpMcW1GMm1HR1lXRlpad01MRkw3MGR0bmNndQ=='

    _YALE_AUTHENTICATION_REFRESH_TOKEN = 'refresh_token'
    _YALE_AUTHENTICATION_ACCESS_TOKEN = 'access_token'

    _REQUEST_PARAM_AREA="area"
    _REQUEST_PARAM_MODE="mode"

    _DEFAULT_REQUEST_TIMEOUT = 5

    def __init__(self, username, password, area_id=1):
        self.username = username
        self.password = password
        self.area_id = area_id

        self._login()

    def get_armed_status(self):
        alarm_state = self._get_authenticated(self._ENDPOINT_GET_MODE)

        return alarm_state.get('data')[0].get('mode')

    def set_armed_status(self, mode):
        params = {
            self._REQUEST_PARAM_AREA: self.area_id,
            self._REQUEST_PARAM_MODE: mode
        }

        return self._post_authenticated(self._ENDPOINT_SET_MODE, params=params)

    def arm_full(self):
        self.set_armed_status(YALE_STATE_ARM_FULL)

    def arm_partial(self):
        self.set_armed_status(YALE_STATE_ARM_PARTIAL)

    def disarm(self):
        self.set_armed_status(YALE_STATE_DISARM)

    def is_armed(self):
        """Return True or False if the system is armed in any way"""
        alarm_code = self.get_armed_status()

        if alarm_code == YALE_STATE_ARM_FULL:
            return True
        elif alarm_code == YALE_STATE_ARM_PARTIAL:
            return True

        return False

    def _get_authenticated(self, endpoint):
        url = self._HOST + endpoint

        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": 'application/x-www-form-urlencoded'
        }

        response = requests.get(url, headers=headers, timeout=self._DEFAULT_REQUEST_TIMEOUT)

        data = response.json()

        if data.get('code') != self.YALE_CODE_RESULT_SUCCESS:
            self._login()
            response = requests.post(url, params=params, timeout=self._DEFAULT_REQUEST_TIMEOUT)
            data = response.json()

        return data

    def _post_authenticated(self, endpoint, params=None):
        url = self._HOST + endpoint

        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": 'application/x-www-form-urlencoded'
        }

        response = requests.post(url, headers=headers, data=params, timeout=self._DEFAULT_REQUEST_TIMEOUT)

        data = response.json()

        if data.get('code') != self.YALE_CODE_RESULT_SUCCESS:
            self._login()
            response = requests.post(url, params=params, timeout=self._DEFAULT_REQUEST_TIMEOUT)
            data = response.json()

        return data

    def _login(self):

        payload = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password
        }
        headers = {
            "Accept": "application/json",
            "Authorization": "Basic " + self._YALE_AUTH_TOKEN,
            "Content-Type": 'application/x-www-form-urlencoded'
        }


        _LOGGER.debug("Attempting login")

        url = self._HOST + self._ENDPOINT_TOKEN

        response = requests.post(url, headers=headers, data=payload, timeout=self._DEFAULT_REQUEST_TIMEOUT)
        data = response.json()
        _LOGGER.debug("Login response: {}".format(data))
        if data.get("error"):
            _LOGGER.debug("Failed to authenticate with Yale Smart Alarm. Error: {}".format(
                data.error_description))
            raise AuthenticationError("Failed to authenticate with Yale Smart Alarm. Check credentials.")

        _LOGGER.info("Login to Yale Alarm API successful.")

        self.refresh_token = data.get(self._YALE_AUTHENTICATION_REFRESH_TOKEN)
        self.access_token = data.get(self._YALE_AUTHENTICATION_ACCESS_TOKEN)
        if self.refresh_token is None or self.access_token is None:
            raise Exception("Failed to authenticate with Yale Smart Alarm. Invalid token.")

        return self.access_token, self.refresh_token
