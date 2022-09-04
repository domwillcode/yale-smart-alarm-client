"""Yale Smart Alarm client is a python client for interacting with the Yale Smart Alarm System API.

See https://github.com/domwillcode/yale-smart-alarm-client for more information.
"""
from __future__ import annotations

import logging
from typing import Any, cast

import time

from .auth import YaleAuth
from .lock import YaleDoorManAPI
from .const import (
    YALE_CODE_RESULT_SUCCESS,
    YALE_STATE_ARM_FULL,
    YALE_STATE_ARM_PARTIAL,
    YALE_STATE_DISARM,
    YALE_LOCK_STATE_LOCKED,
    YALE_LOCK_STATE_UNLOCKED,
    YALE_LOCK_STATE_DOOR_OPEN,
    YALE_LOCK_STATE_UNKNOWN,
    YALE_DOOR_CONTACT_STATE_CLOSED,
    YALE_DOOR_CONTACT_STATE_OPEN,
    YALE_DOOR_CONTACT_STATE_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


class YaleSmartAlarmClient:
    """Module for handling connection with the Yale Smart API."""

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

    def __init__(self, username: str, password: str, area_id: int = 1) -> None:
        """Initialize module."""
        self.auth: YaleAuth = YaleAuth(username=username, password=password)
        self.area_id = area_id
        self.lock_api: YaleDoorManAPI = YaleDoorManAPI(auth=self.auth)

    def get_all(self) -> dict[str, Any]:
        """DEBUG function to get full visibility from API for local testing."""
        devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        mode = self.auth.get_authenticated(self._ENDPOINT_GET_MODE)
        status = self.auth.get_authenticated(self._ENDPOINT_STATUS)
        cycle = self.auth.get_authenticated(self._ENDPOINT_CYCLE)
        online = self.auth.get_authenticated(self._ENDPOINT_ONLINE)
        history = self.auth.get_authenticated(self._ENDPOINT_HISTORY)
        panel_info = self.auth.get_authenticated(self._ENDPOINT_PANEL_INFO)
        auth_check = self.auth.get_authenticated(self._ENDPOINT_CHECK)

        return {
            "DEVICES": devices["data"],
            "MODE": mode["data"],
            "STATUS": status["data"],
            "CYCLE": cycle["data"],
            "ONLINE": online["data"],
            "HISTORY": history["data"],
            "PANEL INFO": panel_info["data"],
            "AUTH CHECK": auth_check["data"],
        }

    def get_all_devices(self, retry: int = 3) -> dict[str, Any]:
        """Return full json for all devices."""
        try:
            devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        except Exception as error:
            _LOGGER.debug(
                "Retry %d on path %s", 4 - retry, self._ENDPOINT_DEVICES_STATUS
            )
            if retry > 0:
                time.sleep(7)
                return self.get_all_devices(retry - 1)
            raise error
        return cast(dict[str, Any], devices["data"])

    def get_cycle(self, retry: int = 3) -> dict[str, Any]:
        """Return full cycle."""
        try:
            cycle = self.auth.get_authenticated(self._ENDPOINT_CYCLE)
        except Exception as error:
            _LOGGER.debug("Retry %d on path %s", 4 - retry, self._ENDPOINT_CYCLE)
            if retry > 0:
                time.sleep(7)
                return self.get_cycle(retry - 1)
            raise error
        return cast(dict[str, Any], cycle["data"])

    def get_status(self, retry: int = 3) -> str:
        """Return status from system."""
        try:
            status = self.auth.get_authenticated(self._ENDPOINT_STATUS)
        except Exception as error:
            _LOGGER.debug("Retry %d on path %s", 4 - retry, self._ENDPOINT_STATUS)
            if retry > 0:
                time.sleep(7)
                return self.get_status(retry - 1)
            raise error
        acfail = status["data"]["acfail"]
        battery = status["data"]["battery"]
        tamper = status["data"]["tamper"]
        jam = status["data"]["jam"]
        if acfail == battery == tamper == jam == "main.normal":
            return "ok"
        return "error"

    def get_online(self, retry: int = 3) -> dict[str, Any]:
        """Return available from system."""
        try:
            online = self.auth.get_authenticated(self._ENDPOINT_ONLINE)
        except Exception as error:
            _LOGGER.debug("Retry %d on path %s", 4 - retry, self._ENDPOINT_ONLINE)
            if retry > 0:
                time.sleep(7)
                return self.get_online(retry - 1)
            raise error
        return cast(dict[str, Any], online["data"])

    def get_panel_info(self, retry: int = 3) -> dict[str, Any]:
        """Return panel information."""
        try:
            panel_info = self.auth.get_authenticated(self._ENDPOINT_PANEL_INFO)
        except Exception as error:
            _LOGGER.debug("Retry %d on path %s", 4 - retry, self._ENDPOINT_PANEL_INFO)
            if retry > 0:
                time.sleep(7)
                return self.get_panel_info(retry - 1)
            raise error
        return cast(dict[str, Any], panel_info["data"])

    def get_history(self, retry: int = 3) -> dict[str, Any]:
        """Return the log from the system."""
        try:
            history = self.auth.get_authenticated(self._ENDPOINT_HISTORY)
        except Exception as error:
            _LOGGER.debug("Retry %d on path %s", 4 - retry, self._ENDPOINT_HISTORY)
            if retry > 0:
                time.sleep(7)
                return self.get_history(retry - 1)
            raise error
        return cast(dict[str, Any], history["data"])

    def get_auth_check(self, retry: int = 3) -> dict[str, Any]:
        """Return the authorization check."""
        try:
            check = self.auth.get_authenticated(self._ENDPOINT_CHECK)
        except Exception as error:
            _LOGGER.debug("Retry %d on path %s", 4 - retry, self._ENDPOINT_CHECK)
            if retry > 0:
                time.sleep(7)
                return self.get_auth_check(retry - 1)
            raise error
        return cast(dict[str, Any], check["data"])

    def get_locks_status(self, retry: int = 3) -> dict[str, str]:
        """Return all locks status from the system."""
        try:
            devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        except Exception as error:
            _LOGGER.debug(
                "Retry %d on path %s", 4 - retry, self._ENDPOINT_DEVICES_STATUS
            )
            if retry > 0:
                time.sleep(7)
                return self.get_locks_status(retry - 1)
            raise error
        locks: dict[str, str] = {}
        for device in devices["data"]:
            if device["type"] == "device_type.door_lock":
                state = device["status1"]
                name = device["name"]
                lock_status_str = device["minigw_lock_status"]
                if lock_status_str != "":
                    lock_status = int(lock_status_str, 16)
                    closed = (lock_status & 16) == 16
                    locked = (lock_status & 1) == 1
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

    def get_doors_status(self, retry: int = 3) -> dict[str, str]:
        """Return all door contacts status from the system."""
        try:
            devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        except Exception as error:
            _LOGGER.debug(
                "Retry %d on path %s", 4 - retry, self._ENDPOINT_DEVICES_STATUS
            )
            if retry > 0:
                time.sleep(7)
                return self.get_doors_status(retry - 1)
            raise error
        doors: dict[str, str] = {}
        for device in devices["data"]:
            if device["type"] == "device_type.door_contact":
                state = device["status1"]
                name = device["name"]
                if "device_status.dc_close" in state:
                    state = YALE_DOOR_CONTACT_STATE_CLOSED
                elif "device_status.dc_open" in state:
                    state = YALE_DOOR_CONTACT_STATE_OPEN
                else:
                    state = YALE_DOOR_CONTACT_STATE_UNKNOWN
                doors[name] = state
        return doors

    def get_armed_status(self, retry: int = 3) -> str:
        """Get armed status."""
        try:
            alarm_state = self.auth.get_authenticated(self._ENDPOINT_GET_MODE)
        except Exception as error:
            _LOGGER.debug("Retry %d on path %s", 4 - retry, self._ENDPOINT_GET_MODE)
            if retry > 0:
                time.sleep(7)
                return self.get_armed_status(retry - 1)
            raise error
        return cast(str, alarm_state.get("data")[0].get("mode"))

    def set_armed_status(self, mode: str) -> bool:
        """Set armed status.

        Arguments:
            mode: Alarm arm state. One of `YALE_STATE_ARM_FULL`, `YALE_STATE_ARM_PARTIAL`,
            or `YALE_STATE_DISARM`.
        Returns:
            Api response from the arm request.
        """
        params = {
            self._REQUEST_PARAM_AREA: self.area_id,
            self._REQUEST_PARAM_MODE: mode,
        }

        response = self.auth.post_authenticated(self._ENDPOINT_SET_MODE, params=params)
        if response["code"] == YALE_CODE_RESULT_SUCCESS:
            return True
        return False

    def trigger_panic_button(self) -> bool:
        """Trigger the alarm via the panic function."""
        response = self.auth.post_authenticated(self._ENDPOINT_PANIC_BUTTON)
        if response["code"] == YALE_CODE_RESULT_SUCCESS:
            return True
        return False

    def arm_full(self) -> bool:
        """Arm away."""
        response = self.set_armed_status(YALE_STATE_ARM_FULL)
        return response

    def arm_partial(self) -> bool:
        """Arm home."""
        response = self.set_armed_status(YALE_STATE_ARM_PARTIAL)
        return response

    def disarm(self) -> bool:
        """Disarm alarm."""
        response = self.set_armed_status(YALE_STATE_DISARM)
        return response

    def is_armed(self) -> bool:
        """Return True or False if the system is armed in any way."""
        armed_status = self.get_armed_status()

        if armed_status == YALE_STATE_ARM_FULL:
            return True
        if armed_status == YALE_STATE_ARM_PARTIAL:
            return True
        return False
