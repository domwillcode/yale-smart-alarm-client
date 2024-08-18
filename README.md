# Yale Smart Alarm Client

[![PyPI version](https://img.shields.io/pypi/v/yalesmartalarmclient.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/yalesmartalarmclient/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/yalesmartalarmclient.svg?logo=python&logoColor=FFE873)](https://pypi.org/project/yalesmartalarmclient/)
[![PyPI downloads](https://img.shields.io/pypi/dm/yalesmartalarmclient.svg)](https://yalesmartalarmclient.org/packages/yalesmartalarmclient)
[![GitHub](https://img.shields.io/github/license/domwillcode/yale-smart-alarm-client)](LICENSE)

Yale Smart Alarm client is a python client for interacting with the Yale Smart Alarm System API.

Supported functions:
- Arm full (away)
- Arm partial (away/night)
- Disarm
- Get alarm status
- Get locks and operate
- Door sensor status
- Trigger alarm panic button

### Usage
Create a client with:

```python
from yalesmartalarmclient.client import YaleSmartAlarmClient

client = YaleSmartAlarmClient(username, password)
```

where username and password are your Yale Smart Alarm credentials.

For full listing of function see functions.md

#### Locks

Iterate the connected locks

```python
client = YaleSmartAlarmClient(username, password)
for lock in client.lock_api.locks():
    print(lock)
```

lock a single lock:

```python
lock = client.lock_api.get(name="myfrontdoor")
lock.close()
```

unlock:

```python
lock = client.lock_api.get(name="myfrontdoor")
lock.open(pin_code="1234566")
```

DEPRECATED! Get connected locks states:

```python
client.get_locks_status()  # Returns an array of locks and status
```


#### Alarms

Change the alarm state with:

```python
client.arm_full()
client.arm_partial()
client.disarm()
```

or

```python
client.set_alarm_state(YALE_STATE_ARM_FULL)
```

where 'mode' is one of:

```python
from yalesmartalarmclient.client import (
    YALE_STATE_ARM_PARTIAL,
    YALE_STATE_DISARM,
    YALE_STATE_ARM_FULL,
)
```

Is the alarm armed fully or partially:

```python
client.is_armed()  # == True
```

or return alarm status. eg.:

```python
client.get_armed_status() is YALE_STATE_ARM_FULL
```

Trigger panic button:

```python
client.trigger_panic_button()
```
