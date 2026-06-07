# V2rayU Node Switching (macOS)

V2rayU stores node configurations in `~/Library/Preferences/net.yanue.V2rayU.plist` as binary plist entries under keys `config.<UUID>`. The active config is written to `~/.V2rayU/config.json` and the core binary at `~/.V2rayU/v2ray-core/v2ray` reads from that.

## How to Switch Nodes

### Method 1: Manual (via macOS menu bar)
1. Click V2rayU menu bar icon
2. Hover over "Server" 
3. Select any node from the list
4. The change takes effect immediately — the core reloads `config.json`

### Method 2: Programmatic via defaults write
Each node is stored as binary plist data under `config.<UUID>` in the preferences. To switch:

```bash
# 1. See what's available
defaults read net.yanue.V2rayU v2rayServerList

# 2. Write desired node UUID to current server key
defaults write net.yanue.V2rayU v2rayCurrentServerName "config.<UUID>"

# 3. Force V2rayU to reload config
# Kill the core process so V2rayU restarts it with the new config
killall V2rayU 2>/dev/null; open -a V2rayU

# Or just kill the core (V2rayU auto-restarts it)
kill $(pgrep -f "~/.V2rayU/v2ray-core/v2ray") 2>/dev/null
```

### Method 3: Decode node details to find a fast one
```python
import plistlib
with open(os.path.expanduser("~/Library/Preferences/net.yanue.V2rayU.plist"), "rb") as f:
    plist = plistlib.load(f)

for key in plist.get("v2rayServerList", []):
    if not key.startswith("config."):
        continue
    data = plist.get(key)
    if isinstance(data, bytes):
        try:
            cfg = plistlib.loads(data)
            print(f"{key}: {cfg.get('remarks', 'unnamed')} - {cfg.get('address')}:{cfg.get('port')} ({cfg.get('protocol')})")
        except:
            print(f"{key}: (binary, could not decode)")
```

## Speed Testing

### Test latency to a specific node
```bash
# Find the node's server address from config.json
grep '"address"' ~/.V2rayU/config.json

# Or test general internet speed through the proxy
curl -x http://127.0.0.1:1087 -s -w "HTTP:%{http_code} Time:%{time_total}s Speed:%{speed_download}B/s\n" \
  -o /dev/null --connect-timeout 10 --max-time 30 \
  "https://httpbin.org/ip"
```

## V2rayU autoSelectFastestServer

The setting `autoSelectFastestServer = 1` is already enabled (stored in the plist). V2rayU periodically tests latency to all nodes and picks the fastest one automatically. However:
- Auto-selection runs on a schedule, not instantly
- It picks based on **latency** (ping time), not **throughput** (download speed)
- A low-latency node may still have low bandwidth for large downloads
- If you're doing a large download (model weights, git clone), try switching manually

## Node List Size

The preferences plist stores all nodes from all subscriptions. This session had **33 config nodes** across the v2rayServerList. The subscribe URL was for **etwang.pages.dev** (a VLESS/WebSocket/TLS endpoint proxied through Cloudflare at 104.17.186.18:8443).

## Pitfalls

- **Binary plist format:** `defaults read` returns the plist content as human-readable strings but the config data under `config.<UUID>` keys is stored as `NSKeyedArchiver` binary blobs. You cannot directly edit these with `defaults write` — you'd need to use plistlib in Python and re-encode.
- **Config overwrite:** When you switch servers via the GUI, V2rayU overwrites `~/.V2rayU/config.json` with the new server's parameters. Any manual edits to config.json are lost on server switch.
- **autoSelectFastestServer + large downloads:** If auto-select is on, it may switch you to a different node mid-download, causing a disconnection. For big downloads, disable auto-select temporarily or switch to a known-good node manually first.
