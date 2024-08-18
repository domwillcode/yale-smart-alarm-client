"""Module for interacting with a Yale Doorman lock."""
from __future__ import annotations

from collections.abc import Iterator
from enum import Enum
from typing import TYPE_CHECKING, Any, cast

from requests import RequestException

from .exceptions import AuthenticationError

if TYPE_CHECKING:
    from .auth import YaleAuth

class YaleLockState(Enum):
    """Lock state enum."""

    LOCKED = 1
    UNLOCKED = 2
    DOOR_OPEN = 3
    UNKNOWN = 4

class YaleLockVolume(Enum):
    """Lock volume enum."""

    HIGH = "03"
    LOW = "02"
    OFF = "01"

class YaleLockConfig:
    """Represents the configuration of a lock."""

    def __init__(self, conf_data: str) -> None:
        """Initialize the lock configuration."""
        self.volume = conf_data[0:2]
        self.autolock = conf_data[2:4]
        self.language = conf_data[8:10]
        self.arm_hold_time = conf_data[30:32]

    def __str__(self) -> str:
        """Return a string representation of the lock configuration."""
        return f"volume: {self.volume}, autolock: {self.autolock}, language: {self.language}, armHoldTime: {self.arm_hold_time}"

    def __eq__(self, other: object) -> bool:
        """Compare two lock configurations."""
        if isinstance(other, self.__class__):
            return (
                self.volume == other.volume
                and self.autolock == other.autolock
                and self.language == other.language
                and self.arm_hold_time == other.arm_hold_time
            )
        return False

    def __ne__(self, other: object) -> bool:
        """Compare two lock configurations."""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Return the hash of the lock configuration."""
        return hash((self.volume, self.autolock, self.language, self.arm_hold_time))

    def to_dict(self) -> dict[str, str]:
        """Return the lock configuration as a dictionary."""
        return {
            "volume": self.volume,
            "autolock": self.autolock,
            "language": self.language,
            "armHoldTime": self.arm_hold_time,
        }

    def to_string(self) -> str:
        """Return the lock configuration as a string."""
        conf = "0" * 32
        conf = conf[:0] + self.volume + conf[2:]
        conf = conf[:2] + self.autolock + conf[4:]
        conf = conf[:8] + self.language + conf[10:]
        conf = conf[:30] + self.arm_hold_time + conf[32:]
        return conf

class YaleLock:
    """This is an abstraction of a remove Yale lock.

    The object created by this class attempts to reflect the remote state,
    and also has the possibility of locking/unlocking the lock state.

    Objects of this class shall usually be created by the lock_api class.
    """

    DEVICE_TYPE: str = "device_type.door_lock"

    def __init__(self, device: dict[str, Any], lock_api: YaleDoorManAPI) -> None:
        """Initialize a Yale lock device."""
        self._lock_api = lock_api
        self._device: dict[str, Any] = device
        self.name: str = device["name"]
        self._config: YaleLockConfig = YaleLockConfig(device["minigw_configuration_data"])
        self._state: YaleLockState = YaleLockState.UNKNOWN
        self.update(device)

    def __eq__(self, other: object) -> bool:
        """Compare two lock objects."""
        if isinstance(other, self.__class__):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return False

    def __str__(self) -> str:
        """Return string representation of a lock."""
        return f"{self.name} [{self.state()}]"

    def update(self, device: dict[str, Any]) -> None:
        """Update the device."""
        self._device = device
        self.name = device["name"]
        self._state = self._calc_state()
        self._config = YaleLockConfig(device["minigw_configuration_data"])

    def state(self) -> YaleLockState:
        """Return the lock state of the lock."""
        return self._state

    def area(self) -> str:
        """Return the lock area."""
        return cast(str, self._device["area"])

    def sid(self) -> str:
        """Return the lock ID."""
        return cast(str, self._device["address"])

    def device_type(self) -> str:
        """Return the lock device type."""
        return cast(str, self._device["type"])

    def zone(self) -> str:
        """Return the lock zone."""
        return cast(str, self._device["no"])

    def set_state(self, new_state: YaleLockState) -> None:
        """Update the device state with new_state."""
        self._state = new_state

    def _calc_state(self) -> YaleLockState:
        raw_state: str = self._device["status1"]

        lock_status_str = self._device["minigw_lock_status"]
        if lock_status_str != "":
            lock_status = int(lock_status_str, 16)
            closed = (lock_status & 16) == 16
            locked = (lock_status & 1) == 1
            if closed is True and locked is True:
                state = YaleLockState.LOCKED
            elif closed is True and locked is False:
                state = YaleLockState.UNLOCKED
            elif not closed:
                state = YaleLockState.DOOR_OPEN
            else:
                state = YaleLockState.UNKNOWN
        elif "device_status.lock" in raw_state:
            state = YaleLockState.LOCKED
        elif "device_status.unlock" in raw_state:
            state = YaleLockState.UNLOCKED
        else:
            state = YaleLockState.UNKNOWN
        return state

    def close(self) -> bool:
        """Attempt to close the remote lock.

        Returns: True if the API returns success.
        """
        try:
            return self._lock_api.close_lock(lock=self)
        except AuthenticationError as error:
            raise error
        except RequestException as error:
            raise error

    def open(self, pin_code: str) -> bool:
        """Attempt to open the lock.

        returns: True if the lock was opened.
        """
        try:
            return self._lock_api.open_lock(lock=self, pin_code=pin_code)
        except AuthenticationError as error:
            raise error
        except RequestException as error:
            raise error

    def set_volume(self, volume: YaleLockVolume) -> bool:
        """Set the volume of the lock.

        Args:
            volume: the new volume. high, low or off.

        Returns:
            True if the operation was a success.

        """
        return self._lock_api.set_volume(lock=self, volume=volume)

    def set_autolock(self, autolock: bool) -> bool:
        """Set the auto lock state of the lock.

        Args:
            autolock: the new state of the auto lock.

        Returns:
            True if the operation was a success.

        """
        return self._lock_api.set_autolock(lock=self, autolock=autolock)

class YaleDoorManAPI:
    """Represents the yale doorman api.

    Example: iterating
        >>> from yalesmartalarmclient.client import YaleSmartAlarmClient
        >>> client = YaleSmartAlarmClient(username="", password="")
        >>> for lock in client.lock_api.locks():
        >>>     print(lock)
        >>>     lock.close()
        >>>     print(lock)
        >>>     lock.open()
        myfrontdoor [YaleLockState.UNLOCKED]
        myfrontdoor [YaleLockState.LOCKED]
        myfrontdoor [YaleLockState.UNLOCKED]

    Example: getting
        >>> from yalesmartalarmclient.client import YaleSmartAlarmClient
        >>> client = YaleSmartAlarmClient(username="", password="")
        >>> lock = client.lock_api.get("myfrondoor"):
        >>> print(lock)
        >>> lock.close()
        >>> print(lock)
        >>> lock.open()
        myfrontdoor [YaleLockState.UNLOCKED]
        myfrontdoor [YaleLockState.LOCKED]
        myfrontdoor [YaleLockState.UNLOCKED]

    """

    CODE_SUCCESS = "000"
    # lock status
    _ENDPOINT_DEVICES_STATUS = "/api/panel/device_status/"
    # lock door
    _ENDPOINT_DEVICES_CONTROL = "/api/panel/device_control/"
    _ENDPOINT_DEVICES_UNLOCK = "/api/minigw/unlock/"
    _ENDPOINT_DEVICES_CONFIG = "/api/minigw/lock/config/"
    _ENDPOINT_DEVICES_UPDATE = "/api/panel/device/"

    def __init__(self, auth: YaleAuth) -> None:
        """Initialize the module."""
        self.auth = auth

    def locks(self) -> Iterator[YaleLock]:
        """Iterate through the locks we have available for this user.

        Yields: the locks

        Example:
            >>> from yalesmartalarmclient.client import YaleSmartAlarmClient
            >>> client = YaleSmartAlarmClient(username="", password="")
            >>> for lock in client.lock_api.locks():
            >>>     print(lock)
            myfrontdoor [YaleLockState.UNLOCKED]

        """
        try:
            devices = self.auth.get_authenticated(self._ENDPOINT_DEVICES_STATUS)
        except AuthenticationError as error:
            raise error
        except RequestException as error:
            raise error
        for device in devices["data"]:
            if device["type"] == YaleLock.DEVICE_TYPE:
                lock = YaleLock(device, lock_api=self)
                yield lock

    def get(self, name: str) -> YaleLock | None:
        """Get a single lock with matching name.

        Args:
            name: The lock name

        Returns:
            An object representing the lock
            or None

        Example:
            >>> from yalesmartalarmclient.client import YaleSmartAlarmClient
            >>> client = YaleSmartAlarmClient(username="", password="")
            >>> lock = client.lock_api.get("myfrontdoor"):
            >>> print(lock)
            myfrontdoor [YaleLockState.UNLOCKED]

        """
        for lock in self.locks():
            if lock == name:
                return lock
        return None

    def close_lock(self, lock: YaleLock) -> bool:
        """Close the specified lock.

        If the operation is successful the lock state will be updated to reflect this.

        Notes:
            the lock object has methods to do this, see YaleLock:close()

        Args:
            lock: The lock you want to close.

        Returns: True if the operation was a success.

        Example:
            >>> from yalesmartalarmclient.client import YaleSmartAlarmClient
            >>> client = YaleSmartAlarmClient(username="", password="")
            >>> lock = client.lock_api.get("myfrontdoor"):
            >>> client.lock_api.close_lock(lock)
            >>> # lock.close() does the same thing!
            >>> print(lock)
            myfrontdoor [YaleLockState.LOCKED]

        """
        params = {
            "area": lock.area(),
            "zone": lock.zone(),
            "device_sid": lock.sid(),
            "device_type": lock.device_type(),
            "request_value": "1",
        }
        try:
            operation_status = self.auth.post_authenticated(
                self._ENDPOINT_DEVICES_CONTROL, params=params
            )
        except AuthenticationError as error:
            raise error
        except RequestException as error:
            raise error

        success: bool = operation_status["code"] == self.CODE_SUCCESS
        if success:
            lock.set_state(YaleLockState.LOCKED)
        return success

    def open_lock(self, lock: YaleLock, pin_code: str) -> bool:
        """Open the specified lock.

        If the operation is a success the local state of lock will be updated to reflect this.

        Notes:
            the lock object has methods to do this, see YaleLock:open()

        Args:
            lock: the lock to open
            pin_code: a valid pin code for the door.

        Returns:
            True if the operation was a success.

        Example:
            >>> from yalesmartalarmclient.client import YaleSmartAlarmClient
            >>> client = YaleSmartAlarmClient(username="", password="")
            >>> lock = client.lock_api.get("myfrontdoor"):
            >>> client.lock_api.open_lock(lock, pin_code="123456")
            >>> # lock.open() does the same thing!
            >>> print(lock)
            myfrontdoor [YaleLockState.UNLOCKED]

        """
        params = {"area": lock.area(), "zone": lock.zone(), "pincode": pin_code}
        try:
            operation_status = self.auth.post_authenticated(
                self._ENDPOINT_DEVICES_UNLOCK, params=params
            )
        except AuthenticationError as error:
            raise error
        except RequestException as error:
            raise error
        success: bool = operation_status["code"] == self.CODE_SUCCESS
        if success:
            lock.set_state(YaleLockState.UNLOCKED)
        return success

    def _put_lock_request(self, lock: YaleLock) -> bool:
        """Api endpoints that seems to be called after device update. Not sure what it does or if it is needed.
        In the yale app it is called after setting auto lock, volume, language, name, when device is deleted, when updateDevice is called (Not sure what that is) and when device is added.
        """
        try:
            operation_status = self.auth.put_authenticated(self._ENDPOINT_DEVICES_UPDATE)
        except AuthenticationError as error:
            raise error
        except RequestException as error:
            raise error
        success: bool = operation_status["code"] == self.CODE_SUCCESS
        return success

    def set_volume(self, lock: YaleLock, volume: YaleLockVolume) -> bool:
        """Set the volume of the lock.

        Args:
            lock: the lock to set the volume for.
            volume: the new volume. high, low or off.

        Returns:
            True if the operation was a success.

        """
        params = {
            "area": lock.area(),
            "zone": lock.zone(),
            "val": volume.value,
            "idx": "01" # Hardcoded value in the app
        }

        operation_status = self.auth.post_authenticated(
            self._ENDPOINT_DEVICES_CONFIG, params=params
        )

        success: bool = operation_status["code"] == self.CODE_SUCCESS
        if success:
            lock._config.volume = volume.value
            # For some reason the app calls _put_lock_request after setting volume
            return self._put_lock_request(lock)
        return success

    def set_autolock(self, lock: YaleLock, autolock: bool) -> bool:
        """Set the auto lock state of the lock.

        Args:
            lock: the lock to set the auto lock state for.
            autolock: the new state of the auto lock.

        Returns:
            True if the operation was a success.

        """
        params = {
            "area": lock.area(),
            "zone": lock.zone(),
            "val": "FF" if autolock else "00", # Hardcoded value in the app
            "idx": "02" # Hardcoded value in the app
        }

        operation_status = self.auth.post_authenticated(
            self._ENDPOINT_DEVICES_CONFIG, params=params
        )

        success: bool = operation_status["code"] == self.CODE_SUCCESS
        if success:
            lock._config.autolock = "FF" if autolock else "00"
            # For some reason the app calls _put_lock_request after setting auto lock
            return self._put_lock_request(lock)
        return success
