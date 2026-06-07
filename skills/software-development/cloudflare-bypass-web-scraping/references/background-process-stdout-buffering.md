# Background Process Stdout Buffering in Hermes

## The Problem

When running a Python script with `terminal(background=True)`, Python detects it's not connected to a TTY and enables full buffering on stdout. This means `print()` output may not appear in Hermes' `process(action='log')` for seconds — or even until the process exits.

This is especially problematic for **interactive login scripts** that:
1. Print "Please scan the QR code" to guide the user
2. Wait 60-120s for manual interaction
3. The agent can't see any output and doesn't know the process is running

## Symptoms

- `process(action='log')` shows empty output
- `process(action='poll')` shows "running" but no output preview
- But `ps aux | grep your_script` shows the process is alive
- And `ps aux | grep chromium` shows the browser process launched

## Fix

Always pass `python3 -u` (unbuffered mode) when running interactive/background scripts:

```bash
# Bad — output may be invisible to Hermes
terminal(background=True, command="python3 ~/.hermes/scripts/myscript.py")

# Good — output appears immediately in process(log=...)
terminal(background=True, command="python3 -u ~/.hermes/scripts/myscript.py")
```

Alternative: set `PYTHONUNBUFFERED=1` in the environment:

```bash
terminal(background=True, command="PYTHONUNBUFFERED=1 python3 ~/.hermes/scripts/myscript.py")
```

## Why This Happens

Python's I/O buffering behavior:
| Output destination | Default buffering |
|---|---|
| TTY (terminal) | Line-buffered |
| Pipe / file / subprocess | Block-buffered (4KB or 8KB) |

`terminal(background=True)` uses pipes to capture stdout, so Python falls into block-buffered mode without `-u` or `PYTHONUNBUFFERED=1`.

## General Rule

**Any Python script that runs as a Hermes background process and produces incremental output should use `python3 -u`.** This includes:
- Login flows (waiting for user interaction)
- Long-running data collection (progress bars, step-by-step logging)
- Watchdog scripts that emit periodic status
