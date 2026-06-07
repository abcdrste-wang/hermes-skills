# Feishu Gateway Configuration

## Multi-Bot Group Chat: `allow_bots`

When multiple bots share a Feishu group, Hermes **silently drops messages from other bots** by default. This is controlled by the `allow_bots` setting.

### How it works

The Feishu adapter's `_admit()` method checks every inbound message. If `sender.sender_type` is `"bot"` or `"app"`, the admission gate queries `self._allow_bots`:

| Value    | Behavior                                                    |
|----------|-------------------------------------------------------------|
| `"none"` | **(default)** Drop all messages from other bots silently    |
| `"mentions"` | Only admit bot messages that @-mention Hermes          |
| `"all"`  | Admit every message from other bots                         |

### Where to set it

**Option A — config.yaml** (recommended):
```yaml
feishu:
  allow_bots: all       # or "mentions"
```

**Option B — environment variable**:
```bash
export FEISHU_ALLOW_BOTS=all
```

The config.yaml value is bridged into the env var at gateway config load (`gateway/config.py` line 1148-1149`). Env var takes precedence if both are set.

### Pitfalls

- **Default is `"none"`** — the first time someone puts Hermes in a group with another bot, bot messages will be invisible. This catches nearly everyone.
- **Restart required** — `FEISHU_ALLOW_BOTS` is read once at adapter init. Change → `/restart` (gateway) or restart CLI.
- **Feishu platform may not forward bot messages at all** — even with `allow_bots: all`, Feishu's Open Platform may choose not to push `im.message.receive_v1` events where the sender is a bot from a different app. This is a Feishu-side limitation, not a Hermes bug. If `allow_bots: all` doesn't work:
  1. Confirm the other bot has a different App ID (different apps are more likely to be forwarded)
  2. Check Feishu Open Platform console for any bot-message filtering settings
  3. Check `~/.hermes/logs/gateway.log` for `dropping inbound event: bots_disabled` or `dropping inbound event: self_echo` — these confirm the message reached Hermes but was filtered

### Source

- `gateway/platforms/feishu.py` line 394: `allow_bots: str = "none"`
- `gateway/platforms/feishu.py` line 1502: env var read: `os.getenv("FEISHU_ALLOW_BOTS", "none")`
- `gateway/platforms/feishu.py` line 3942-3976: `_admit()` admission logic
- `gateway/config.py` line 1148-1149: yaml → env var bridge
