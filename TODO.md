
## Log file for adopted processes

**Status**: ✅ Fixed

**Issue**: When a daemon is adopted (already running), `log_file` wasn't set and output wasn't captured.

**Symptoms**: `procler logs detectd` returned empty because:
1. Process was adopted, not started fresh
2. No log_file path was set during adoption
3. No redirect was added to the command (daemon already running)

**Solution implemented**:
1. On adoption, `log_file` path is now set (even though we can't redirect the already-running daemon's output)
2. Status output now includes `adopted: true` for adopted processes
3. Logs response includes a helpful `note` when logs are empty for adopted processes, explaining the workaround

**Remaining limitation**: Historical logs from before adoption are not available because we cannot redirect output from an already-running process.

**Workaround for users who need logs**: Restart the process via procler:
```bash
procler restart detectd
procler restart webd
```
