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

YALE_LOCK_STATE_LOCKED = "locked"
YALE_LOCK_STATE_UNLOCKED = "unlocked"
YALE_LOCK_STATE_DOOR_OPEN = "dooropen"
YALE_LOCK_STATE_UNKNOWN = "unknown"

class AuthenticationError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class YaleSmartAlarmClient:
    YALE_CODE_RESULT_SUCCESS = '000'

    _HOST = "https://mob.yalehomesystem.co.uk/yapi"
    _ENDPOINT_TOKEN = "/o/token/"
    _ENDPOINT_SERVICES = "/services/"
    _ENDPOINT_GET_MODE = "/api/panel/mode/"
    _ENDPOINT_SET_MODE = "/api/panel/mode/"
    _ENDPOINT_DEVICES_STATUS = "/api/panel/device_status/"

    _YALE_AUTH_TOKEN = 'VnVWWDZYVjlXSUNzVHJhcUVpdVNCUHBwZ3ZPakxUeXNsRU1LUHBjdTpkd3RPbE15WEtENUJ5ZW1GWHV0am55eGhrc0U3V0ZFY2p0dFcyOXRaSWNuWHlSWHFsWVBEZ1BSZE1xczF4R3VwVTlxa1o4UE5ubGlQanY5Z2hBZFFtMHpsM0h4V3dlS0ZBcGZzakpMcW1GMm1HR1lXRlpad01MRkw3MGR0bmNndQ=='

    _YALE_AUTHENTICATION_REFRESH_TOKEN = 'refresh_token'
    _YALE_AUTHENTICATION_ACCESS_TOKEN = 'access_token'

    _REQUEST_PARAM_AREA = "area"
    _REQUEST_PARAM_MODE = "mode"

    _DEFAULT_REQUEST_TIMEOUT = 5

    def __init__(self, username, password, area_id=1):
        self.username = username
        self.password = password
        self.area_id = area_id
        self.refresh_token = None
        
        self._authorize()

    @property
    def auth_headers(self):
        return {
            "Authorization": "Bearer " + self.access_token
        }
        
    @property
    def get_locks_status(self):
        devices = self._get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        locks = {}
        for device in devices['data']:
            if device['type'] == "device_type.door_lock":
                state = device['status1']
                name = device['name']
                lock_status_str = device['minigw_lock_status']
                if lock_status_str != '':
                    lock_status = int(lock_status_str, 16)
                    closed = ((lock_status & 16) == 16)
                    locked = ((lock_status & 1) == 1)
                    if closed is True and locked is True:
                        state = YALE_LOCK_STATE_LOCKED
                    elif closed is True and locked is False:
                        state = YALE_LOCK_STATE_UNLOCKED
                    elif not closed:
                        state = YALE_LOCK_STATE_DOOR_OPEN
                elif "device_status.lock" in state:
                    state = YALE_LOCK_STATE_LOCKED
                elif "device_status.unlock" in state:
                    state = YALE_LOCK_STATE_UNLOCKED
                else:
                    state = YALE_LOCK_STATE_UNKNOWN
                locks[name] = state
        return locks

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

        if alarm_code == YALE_STATE_ARM_PARTIAL:
            return True

        return False

    def _get_authenticated(self, endpoint):
        url = self._HOST + endpoint
        response = requests.get(url, headers=self.auth_headers, timeout=self._DEFAULT_REQUEST_TIMEOUT)
        if response.status_code != 200:
            self._authorize()
            response = requests.get(url, headers=self.auth_headers, timeout=self._DEFAULT_REQUEST_TIMEOUT)

        return response.json()

    def _post_authenticated(self, endpoint, params=None):
        url = self._HOST + endpoint
        response = requests.post(url, headers=self.auth_headers, data=params, timeout=self._DEFAULT_REQUEST_TIMEOUT)
        if response.status_code != 200:
            self._authorize()
            response = requests.post(url, headers=self.auth_headers, data=params, timeout=self._DEFAULT_REQUEST_TIMEOUT)

        return response.json()

    def _update_services(self):
        data = self._get_authenticated(self._ENDPOINT_SERVICES)
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
        data = response.json()
        _LOGGER.debug("Authorization response: %s", data)
        if data.get("error"):
            if self.refresh_token:
                # Maybe refresh_token has expired, try again with password
                self.refresh_token = None
                return self._authorize()
            _LOGGER.debug("Failed to authenticate with Yale Smart Alarm. Error: %s", data.error_description)
            raise AuthenticationError("Failed to authenticate with Yale Smart Alarm. Check credentials.")

        _LOGGER.info("Authorization to Yale Alarm API successful.")

        self.refresh_token = data.get(self._YALE_AUTHENTICATION_REFRESH_TOKEN)
        self.access_token = data.get(self._YALE_AUTHENTICATION_ACCESS_TOKEN)
        if self.refresh_token is None or self.access_token is None:
            raise Exception("Failed to authenticate with Yale Smart Alarm. Invalid token.")

        self._update_services()
        return self.access_token, self.refresh_token
