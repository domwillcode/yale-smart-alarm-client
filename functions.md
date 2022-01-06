# Yale Smart Alarm Client

## Listing of all functions available

### Usage

Create a client with:
```
from yalesmartalarmclient.client import YaleSmartAlarmClient
client = YaleSmartAlarmClient(username, password)
```
where username and password are your Yale Smart Alarm credentials.

#### Client functions

Debug output for command line (returns long string):
```python
client.get_all()
```

Return full json all devices (does not include the alarm itself):
```python
client.get_all_devices()
```

Returns full json all devices, status of alarm and reports/alarms:
```python
client.get_cycle()
```

Returns full json health status of system:
```python
client.get_status()
```

Returns full json system available/online:
```python
client.get_online()
```

Returns full json panel (alarm) information:
```python
client.get_panel_info()
```

Returns full json first page of history (log):
```python
client.get_history()
```

Returns full json for authentication info:
```python
client.get_auth_check()
```

Returns reduced json lock status:
```python
client.get_locks_status()
```

Returns reduced json door contacts status:
```python
client.get_doors_status()
```

Returns api status of alarm:
```python
client.get_armed_status()
```

Set status of alarm:
```python
client.set_armed_status(mode)
```

Trigger panic button:
```python
client.trigger_panic_button()
```

Arm away:
```python
client.arm_full()
```

Arm home:
```python
client.arm_partial()
```

Disarm:
```python
client.disarm()
```

Return true/false on alarm on/off:
```python
client.is_armed()
```


