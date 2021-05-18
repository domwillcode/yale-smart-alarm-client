#!/usr/bin/env python
"""Yale Smart Alarm client is a python client for interacting with the Yale Smart Alarm System API.

See https://github.com/domwillcode/yale-smart-alarm-client for more information.
"""

import logging
from .auth import YaleAuth
from .lock import YaleDoorManAPI

_LOGGER = logging.getLogger(__name__)

YALE_STATE_ARM_FULL = "arm"
YALE_STATE_ARM_PARTIAL = "home"
YALE_STATE_DISARM = "disarm"

YALE_LOCK_STATE_LOCKED = "locked"
YALE_LOCK_STATE_UNLOCKED = "unlocked"
YALE_LOCK_STATE_DOOR_OPEN = "dooropen"
YALE_LOCK_STATE_UNKNOWN = "unknown"

YALE_DOOR_CONTACT_STATE_CLOSED = "closed"
YALE_DOOR_CONTACT_STATE_OPEN = "open"
YALE_DOOR_CONTACT_STATE_UNKNOWN = "unknown"


class AuthenticationError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class YaleSmartAlarmClient:
    YALE_CODE_RESULT_SUCCESS = '000'

    _ENDPOINT_GET_MODE = "/api/panel/mode/"
    _ENDPOINT_SET_MODE = "/api/panel/mode/"
    _ENDPOINT_DEVICES_STATUS = "/api/panel/device_status/"
    _ENDPOINT_PANIC_BUTTON = "/api/panel/panic"
    _ENDPOINT_STATUS = "/yapi/api/panel/status/"
    _ENDPOINT_CYCLE = "/yapi/api/panel/cycle/"
    _ENDPOINT_ONLINE = "/yapi/api/panel/online/"
    _ENDPOINT_HISTORY = "/yapi/api/event/report/?page_num=1&set_utc=1"

    _REQUEST_PARAM_AREA = "area"
    _REQUEST_PARAM_MODE = "mode"

    _DEFAULT_REQUEST_TIMEOUT = 5

    def __init__(self, username, password, area_id=1):
        self.auth: YaleAuth = YaleAuth(username=username, password=password)
        self.area_id = area_id
        self.lock_api: YaleDoorManAPI = YaleDoorManAPI(auth=self.auth)

    # Included to get full visibility from API for local testing, use with print()
    def get_all(self):
        devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        mode = self.auth.get_authenticated(self._ENDPOINT_GET_MODE)
        status = self.auth.get_authenticated(self._ENDPOINT_STATUS)
        cycle = self.auth.get_authenticated(self._ENDPOINT_CYCLE)
        online = self.auth.get_authenticated(self._ENDPOINT_ONLINE)
        history = self.auth.get_authenticated(self._ENDPOINT_HISTORY)

        return "DEVICES \n" + str(devices) + "\n MODE \n" + str(mode) + "\n STATUS \n" + str(status) + "\n CYCLE \n" + str(cycle) + "\n ONLINE \n" + str(online) + "\n HISTORY \n" + str(history)

    def get_all_devices(self):
        """Return full json for all devices"""
        devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        return devices

    def get_cycle(self):
        """Return full cycle."""
        cycle = self.auth.get_authenticated(self._ENDPOINT_CYCLE)
        return cycle

    def get_status(self):
        """Return status from system."""
        status = self.auth.get_authenticated(self._ENDPOINT_STATUS)
        acfail = status['data']['acfail']
        battery = status['data']['battery']
        tamper = status['data']['tamper']
        jam = status['data']['jam']
        if acfail == battery == tamper == jam == "main.normal":
            return "ok"
        return "error"

    def get_online(self):
        """Return available from system."""
        online = self.auth.get_authenticated(self._ENDPOINT_ONLINE)
        return online['data']

    def get_history(self):
        """Return the log from the system."""
        history = self.auth.get_authenticated(self._ENDPOINT_HISTORY)
        return history

    def get_locks_status(self):
        devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
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

    def get_doors_status(self):
        devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        doors = {}
        for device in devices['data']:
            if device['type'] == "device_type.door_contact":
                state = device['status1']
                name = device['name']
                if "device_status.dc_close" in state:
                    state = YALE_DOOR_CONTACT_STATE_CLOSED
                elif "device_status.dc_open" in state:
                    state = YALE_DOOR_CONTACT_STATE_OPEN
                else:
                    state = YALE_DOOR_CONTACT_STATE_UNKNOWN
                doors[name] = state
        return doors

    def get_armed_status(self):
        alarm_state = self.auth.get_authenticated(self._ENDPOINT_GET_MODE)
        return alarm_state.get('data')[0].get('mode')

    def set_armed_status(self, mode):
        params = {
            self._REQUEST_PARAM_AREA: self.area_id,
            self._REQUEST_PARAM_MODE: mode
        }

        return self.auth.post_authenticated(self._ENDPOINT_SET_MODE, params=params)

    def trigger_panic_button(self):
        self.auth.post_authenticated(self._ENDPOINT_PANIC_BUTTON)

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
