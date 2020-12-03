# Yale Smart Alarm Client
Yale Smart Alarm client is a python client for interacting with the Yale Smart Alarm System API.

Supported functions:
- Arm full (away)
- Arm partial (away/night)
- Disarm
- Get alarm status

### Usage
Create a client with:
```
from yalesmartalarmclient.client import YaleSmartAlarmClient
client = YaleSmartAlarmClient(username, password)
```
where username and password are your Yale Smart Alarm credentials.

#### Locks
Iterate the connected locks
```pyhon
client = YaleClient(username, password)
for lock in client.lock_api.locks():
    print(lock)
```

lock a single lock
```pyhon
lock = client.lock_api.get(name="myfrontdoor"):
lock.close()
```

unlock:
```pyhon
lock = client.lock_api.get(name="myfrontdoor"):
lock.open(pin_code="1234566")
```

DEPRECATED! Get connected locks states:
```
client.get_locks_status() # Returns an array of locks and status
```


#### Alarms
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

Trigger panic button
```
client.trigger_panic_button()
```


