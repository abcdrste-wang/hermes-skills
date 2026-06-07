# Steam in China — Network Diagnostics

Steam has a **split network architecture** that behaves differently under the GFW:

| Component | Status in China | Protocol | Works with Proxy |
|-----------|----------------|----------|-----------------|
| **Login/Session** (CM servers) | ✅ Works | WebSocket :443 | Yes |
| **Store pages** | ❌ Blocked | HTTPS | Yes (V2rayU) |
| **Game downloads** (CDN) | ❌ Blocked | HTTPS / SteamPipe | Partially (slow) |
| **Matchmaking / Multiplayer** | ✅ Usually works | UDP / WebSocket | Varies by game |

## Where to Check

### Process
```bash
ps aux | grep -i steam
# → /Applications/Steam.app/Contents/MacOS/steam_osx if running
```

### Application Path
- Executable: `/Applications/Steam.app`
- Data dir: `~/Library/Application Support/Steam/`

### Key Log Files (under `~/Library/Application Support/Steam/logs/`)

| Log | What It Tells You |
|-----|-------------------|
| `connection_log.txt` | Login status, CM server ping (who it connected to, latency) |
| `content_log.txt` | Download server health — shows **"Failed to get list of download sources"** when CDN is blocked |
| `bootstrap_log.txt` | Startup sequence, update checks |
| `cef_log.txt` | Steam UI rendering (mostly noise — `ffmpeg_common.cc: unsupported pixel format` is harmless) |
| `gameprocess_log.txt` | Game launch/crash diagnostics |

### Game Installation State
```bash
# List installed games
ls ~/Library/Application\ Support/Steam/steamapps/common/

# Check library folders (can have multiple)
cat ~/Library/Application\ Support/Steam/steamapps/libraryfolders.vdf

# Check app manifests (one per installed game, numeric Steam App ID)
ls ~/Library/Application\ Support/Steam/steamapps/appmanifest_*.acf
```

## China-Specific Patterns

### Login Works, Downloads Don't (the classic pattern)

This is the most common finding for Steam users in China:

```
connection_log.txt → [Logged On] 'OK'  ✅
content_log.txt    → Failed to get list of download sources  ❌
```

The user can log in, browse their library, and play games that are already installed. But:
- **New game installs / updates fail** — the CDN servers (`steamcontent.com`, `steampipe.steamcontent.com`) are blocked by the GFW
- **Store / Community pages don't load** (these are also blocked)
- **Login works** because Steam's CM (Connection Manager) servers use WebSocket :443 which proxies handle well

CM server connection example from logs:
```
cmp1-dfw2.steamserver.net:443 → 196.7773ms → Connected  ✅ (via Dallas, not blocked)
```

### Workarounds

1. **V2rayU proxy (HTTP 1087 / SOCKS5 1080)**
   - Set Steam → Settings → In-Game → Browser proxy to `http://127.0.0.1:1087`
   - Or use a system-level proxy that covers Steam's traffic
   - Note: Game downloads through proxy can be **very slow** for large files (proxy bandwidth limit)

2. **Steam China client (蒸汽平台)**
   - Not compatible with international Steam account/games
   - Separate client, separate store

3. **Steam++ / Watt Toolkit** (third-party)
   - Tool specifically designed to accelerate Steam access from China
   - Handles local host file patches and proxy routing for Steam CDNs

4. **Download then install** pattern
   - Download the game from an alternative source (e.g., repack sites via direct download)
   - Place files in `steamapps/common/<game>/` then "Install" through Steam client
   - Steam will verify existing files instead of re-downloading

## Quick Diagnostic Script

```bash
#!/bin/bash
echo "=== Steam Process ==="
pgrep -fli steam || echo "Not running"

echo ""
echo "=== Steam App ==="
ls -d /Applications/Steam.app 2>/dev/null || echo "Not found at /Applications"

echo ""
echo "=== Game Installations ==="
ls ~/Library/Application\ Support/Steam/steamapps/common/ 2>/dev/null || echo "No games directory"

echo ""
echo "=== Login Log (last 10 lines) ==="
tail -10 ~/Library/Application\ Support/Steam/logs/connection_log.txt 2>/dev/null || echo "No connection log"

echo ""
echo "=== Content Server Errors ==="
grep -i "fail" ~/Library/Application\ Support/Steam/logs/content_log.txt 2>/dev/null || echo "No errors"
```

Run from terminal to get a quick overview of Steam health on macOS.
