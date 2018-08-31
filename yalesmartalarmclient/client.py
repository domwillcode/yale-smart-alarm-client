#!/usr/bin/env python
"""Yale Smart Alarm client is a python client for interacting with the Yale Smart Alarm System API.
"""

import logging
import requests

_LOGGER = logging.getLogger(__name__)

YALE_STATE_ARM_FULL = "arm"
YALE_STATE_ARM_PARTIAL = "home"
YALE_STATE_DISARM = "disarm"


class YaleSmartAlarmClient:
    YALE_CODE_AUTHENTICATION_ERROR = '999'
    YALE_CODE_RESULT_SUCCESS = '1'
    YALE_CODE_RESULT_FAIL = '0'

    YALE_AUTHENTICATION_TOKEN_NAME = 'PHPSESSID'

    _ENDPOINT_LOGIN = "https://www.yalehomesystem.co.uk/homeportal/api/login/check_login/"
    _ENDPOINT_LOGOUT = "https://www.yalehomesystem.co.uk/homeportal/api/logout/"
    _ENDPOINT_GET_MODE = "https://www.yalehomesystem.co.uk/homeportal/api/panel/get_panel_mode"
    _ENDPOINT_SET_MODE = "https://www.yalehomesystem.co.uk/homeportal/api/panel/set_panel_mode"

    _REQUEST_PARAM_AREA="area"
    _REQUEST_PARAM_MODE="mode"

    def __init__(self, username, password, area_id=1):
        self.username = username
        self.password = password
        self.area_id = area_id

        self._login()

    def close(self):
        self._logout()

    def get_armed_status(self):
        params = {
            self._REQUEST_PARAM_AREA: self.area_id
        }

        alarm_state = self._post_authenticated(self._ENDPOINT_GET_MODE, params=params)
        return alarm_state.get('message')[0].get('mode')

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

    def _post_authenticated(self, endpoint, params=None):
        response = requests.post(endpoint, params=params, cookies=self.cookies)
        data = response.json()
        if data.get('code') == self.YALE_CODE_AUTHENTICATION_ERROR:
            self._login()
            response = requests.post(endpoint, params=params, cookies=self.cookies)
            data = response.json()

        return data

    def _login(self):
        payload = {
            "id": self.username,
            "password": self.password
        }

        _LOGGER.debug("Attempting login")

        response = requests.post(self._ENDPOINT_LOGIN, data=payload)

        data = response.json()
        _LOGGER.debug("Login reponse: {}".format(data))
        if data.get("result") is not self.YALE_CODE_RESULT_SUCCESS:
            raise Exception("Failed to authenticate with Yale Smart Alarm. Expecting result code {} in {}".format(
                            self.YALE_CODE_RESULT_SUCCESS, data))

        _LOGGER.info("Login to Yale Alarm API successful.")

        self.token = response.cookies.get(self.YALE_AUTHENTICATION_TOKEN_NAME)
        if self.token is None:
            raise Exception("Failed to authenticate with Yale Smart Alarm. Invalid token.")

        self.cookies = self._generate_cookies(self.token)

        return self.token

    def _logout(self):
        requests.post(self._ENDPOINT_LOGOUT, cookies=self.cookies)
        _LOGGER.info("Logged out of Yale Alarm API")

    def _generate_cookies(self, token):
        cookies = requests.cookies.RequestsCookieJar()
        cookies.set(self.YALE_AUTHENTICATION_TOKEN_NAME, token)
        return cookies
