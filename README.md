# Yale Smart Alarm Client
Yale Smart Alarm client is a python client for interacting with the Yale Smart Alarm System API.

Supported functions:
- Arm full (away)
- Arm partial (away/night)
- Disarm
- Get alarm status

#### Usage
Create a client with:
```
from yalesmartalarmclient.client import YaleSmartAlarmClient
client = YaleSmartAlarmClient(username, password)
```
where username and password are your Yale Smart Alarm credentials.

Change the alarm state with:
```
client.arm_full()
client.arm_partial()
client.disarm()
```
or 
```
client.set_alarm_state(<mode>)
```
where 'mode' is one of:
```
from yalesmartalarmclient.client import (YALE_STATE_ARM_PARTIAL,
                                         YALE_STATE_DISARM,
                                         YALE_STATE_ARM_FULL)
```

Is the alarm armed fully or partially:
```
client.is_armed() # == True
```

or return alarm status. eg.
```
client.get_armed_status() is YALE_STATE_ARM_FULL
```
