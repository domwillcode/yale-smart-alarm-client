#!/usr/bin/env python
"""Yale Smart Alarm client is a python client for interacting with the Yale Smart Alarm System API.

See https://github.com/domwillcode/yale-smart-alarm-client for more information.
"""

import logging
from .auth import YaleAuth
from .lock import YaleDoorManAPI
from .exceptions import AuthenticationError, ConnectionError

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
    _ENDPOINT_CHECK = "/yapi/api/auth/check/"
    _ENDPOINT_PANEL_INFO = "/yapi/api/panel/info/"

    _REQUEST_PARAM_AREA = "area"
    _REQUEST_PARAM_MODE = "mode"

    _DEFAULT_REQUEST_TIMEOUT = 5

    def __init__(self, username, password, area_id=1):
        self.auth: YaleAuth = YaleAuth(username=username, password=password)
        self.area_id = area_id
        self.lock_api: YaleDoorManAPI = YaleDoorManAPI(auth=self.auth)

    def get_all(self):
        """DEBUG function to get full visibility from API for local testing, use with print()."""
        try:
            devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
            mode = self.auth.get_authenticated(self._ENDPOINT_GET_MODE)
            status = self.auth.get_authenticated(self._ENDPOINT_STATUS)
            cycle = self.auth.get_authenticated(self._ENDPOINT_CYCLE)
            online = self.auth.get_authenticated(self._ENDPOINT_ONLINE)
            history = self.auth.get_authenticated(self._ENDPOINT_HISTORY)
            panel_info = self.auth.get_authenticated(self._ENDPOINT_PANEL_INFO)
            auth_check = self.auth.get_authenticated(self._ENDPOINT_CHECK)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError

        return (
            " DEVICES \n" + str(devices['data']) + "\n MODE \n" + str(mode['data']) + "\n STATUS \n" + str(status['data']) +
            "\n CYCLE \n" + str(cycle['data']) + "\n ONLINE \n" + str(online['data']) + "\n HISTORY \n" + str(history['data']) +
            "\n PANEL INFO \n" + str(panel_info['data']) + "\n AUTH CHECK \n" + str(auth_check['data'])
        )

    def get_all_devices(self):
        """Return full json for all devices"""
        try:
            devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
        return devices['data']

    def get_cycle(self):
        """Return full cycle."""
        try:
            cycle = self.auth.get_authenticated(self._ENDPOINT_CYCLE)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
        return cycle['data']

    def get_status(self):
        """Return status from system."""
        try:
            status = self.auth.get_authenticated(self._ENDPOINT_STATUS)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
        acfail = status['data']['acfail']
        battery = status['data']['battery']
        tamper = status['data']['tamper']
        jam = status['data']['jam']
        if acfail == battery == tamper == jam == "main.normal":
            return "ok"
        return "error"

    def get_online(self):
        """Return available from system."""
        try:
            online = self.auth.get_authenticated(self._ENDPOINT_ONLINE)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
        return online['data']

    def get_panel_info(self):
        """Return panel information."""
        try:
            panel_info = self.auth.get_authenticated(self._ENDPOINT_PANEL_INFO)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
        return panel_info['data']

    def get_history(self):
        """Return the log from the system."""
        try:
            history = self.auth.get_authenticated(self._ENDPOINT_HISTORY)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
        return history['data']

    def get_auth_check(self):
        """Return the authorization check."""
        try:
            check = self.auth.get_authenticated(self._ENDPOINT_CHECK)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
        return check['data']

    def get_locks_status(self):
        """Return all locks status from the system."""
        try:
            devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
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
        """Return all door contacts status from the system."""
        try:
            devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
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
        """ Get armed status."""
        try:
            alarm_state = self.auth.get_authenticated(self._ENDPOINT_GET_MODE)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError
        return alarm_state.get('data')[0].get('mode')

    def set_armed_status(self, mode):
        params = {
            self._REQUEST_PARAM_AREA: self.area_id,
            self._REQUEST_PARAM_MODE: mode
        }

        try:
            return self.auth.post_authenticated(self._ENDPOINT_SET_MODE, params=params)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError

    def trigger_panic_button(self):
        """Trigger the alarm via the panic function."""
        try:
            self.auth.post_authenticated(self._ENDPOINT_PANIC_BUTTON)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError

    def arm_full(self):
        """Arm away."""
        try:
            self.set_armed_status(YALE_STATE_ARM_FULL)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError

    def arm_partial(self):
        """Arm home."""
        try:
            self.set_armed_status(YALE_STATE_ARM_PARTIAL)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError

    def disarm(self):
        """Disarm alarm."""
        try:
            self.set_armed_status(YALE_STATE_DISARM)
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError

    def is_armed(self):
        """Return True or False if the system is armed in any way"""
        try:
            alarm_code = self.get_armed_status()
        except AuthenticationError:
            raise AuthenticationError
        except:
            raise ConnectionError

        if alarm_code == YALE_STATE_ARM_FULL:
            return True

        if alarm_code == YALE_STATE_ARM_PARTIAL:
            return True

        return False
