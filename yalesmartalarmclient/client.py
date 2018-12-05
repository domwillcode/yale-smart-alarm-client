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

        self._login()

    def get_doorman_state(self):
        devices = self._get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        list = []
        for dev in devices['data']:
            if dev['type'] == "device_type.door_lock":
                state = dev['status1']
                name = dev['name']
                lock_status_str = dev['minigw_lock_status']
                if lock_status_str != '':
                    lock_status = int(lock_status_str, 16)
                    closed = ((lock_status & 16) == 16)
                    locked = ((lock_status & 1) == 1)
                    if closed == True and locked == True:
                        state = "Locked"
                    elif closed == True and locked == False:
                        state = "Unlocked"
                    elif closed == False:
                        state = "Door open"
                elif "device_status.lock" in state:
                    state = "Locked"
                elif "device_status.unlock" in state:
                    state = "Unlocked"
                else:
                    state = "Unknown"
                list.append({name:state})
        return list

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

        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": 'application/x-www-form-urlencoded'
        }

        response = requests.get(url, headers=headers, timeout=self._DEFAULT_REQUEST_TIMEOUT)

        data = response.json()

        if data.get('code') != self.YALE_CODE_RESULT_SUCCESS:
            self._login()
            response = requests.get(url, timeout=self._DEFAULT_REQUEST_TIMEOUT)
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

    def _get_services(self):
        url = self._HOST + self._ENDPOINT_SERVICES

        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": 'application/x-www-form-urlencoded'
        }

        _LOGGER.debug("Fetch services URL")

        response = requests.get(url, headers=headers, timeout=self._DEFAULT_REQUEST_TIMEOUT)
        data = response.json()
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
        _LOGGER.debug("Login response: %s", data)
        if data.get("error"):
            _LOGGER.debug("Failed to authenticate with Yale Smart Alarm. Error: %s", data.error_description)
            raise AuthenticationError("Failed to authenticate with Yale Smart Alarm. Check credentials.")

        _LOGGER.info("Login to Yale Alarm API successful.")

        self.refresh_token = data.get(self._YALE_AUTHENTICATION_REFRESH_TOKEN)
        self.access_token = data.get(self._YALE_AUTHENTICATION_ACCESS_TOKEN)
        if self.refresh_token is None or self.access_token is None:
            raise Exception("Failed to authenticate with Yale Smart Alarm. Invalid token.")

        self._get_services()
        return self.access_token, self.refresh_token
