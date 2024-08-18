"""Python client for Yale Smart Living."""

from .auth import YaleAuth
from .client import YaleSmartAlarmClient, YaleSmartAlarmData
from .const import (
    YALE_DOOR_CONTACT_STATE_CLOSED,
    YALE_DOOR_CONTACT_STATE_OPEN,
    YALE_DOOR_CONTACT_STATE_UNKNOWN,
    YALE_LOCK_STATE_DOOR_OPEN,
    YALE_LOCK_STATE_LOCKED,
    YALE_LOCK_STATE_UNKNOWN,
    YALE_LOCK_STATE_UNLOCKED,
    YALE_STATE_ARM_FULL,
    YALE_STATE_ARM_PARTIAL,
    YALE_STATE_DISARM,
)
from .exceptions import AuthenticationError, UnknownError
from .lock import (
    YaleDoorManAPI,
    YaleLock,
    YaleLockConfig,
    YaleLockState,
    YaleLockVolume,
)

__all__ = [
    "YaleAuth",
    "YaleSmartAlarmData",
    "YaleSmartAlarmClient",
    "YALE_STATE_ARM_FULL",
    "YALE_STATE_ARM_PARTIAL",
    "YALE_STATE_DISARM",
    "YALE_LOCK_STATE_LOCKED",
    "YALE_LOCK_STATE_UNLOCKED",
    "YALE_LOCK_STATE_DOOR_OPEN",
    "YALE_LOCK_STATE_UNKNOWN",
    "YALE_DOOR_CONTACT_STATE_CLOSED",
    "YALE_DOOR_CONTACT_STATE_OPEN",
    "YALE_DOOR_CONTACT_STATE_UNKNOWN",
    "AuthenticationError",
    "UnknownError",
    "YaleLockState",
    "YaleLockVolume",
    "YaleLockConfig",
    "YaleLock",
    "YaleDoorManAPI",
]
