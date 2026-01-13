
## Log file for adopted processes

**Issue**: When a daemon is adopted (already running), `log_file` isn't set and output isn't captured.

**Symptoms**: `procler logs detectd` returns empty because:
1. Process was adopted, not started fresh
2. No log_file path was set during adoption
3. No redirect was added to the command

**Potential fixes**:
1. **Simple**: User restarts process via procler to get logs (`procler restart detectd`)
2. **Better**: On adoption, set `log_file` path and note that historical logs aren't available
3. **Advanced**: For docker daemons, check if process writes to a known log location and tail that

**Workaround**: Restart the process via procler:
```bash
procler restart detectd
procler restart webd
```
