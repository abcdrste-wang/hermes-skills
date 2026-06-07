---
name: steam-macos
description: "Manage Steam on macOS: install, configure, troubleshoot, run Windows games via Whisky/CrossOver, navigate Chinese network restrictions."
version: 1.0.0
author: agent
platforms: [macos]
metadata:
  hermes:
    tags: [steam, gaming, macos, whisky, crossover, windows-compatibility, china-network]
---

# Steam on macOS

Manage Steam on macOS — from game installation to troubleshooting and running Windows-only games through compatibility layers.

## Running Steam Behind Proxy (China)

- **Login/Community**: Works through HTTP/SOCKS proxy (V2rayU). Connects to Steam WebSocket via Dallas/LAX nodes (~196ms from China).
- **Game Downloads (content servers)**: `cdn.steamcontent.com` servers are often blocked in China directly. Use proxy with global/rule mode for game downloads.
- **Client updates**: Work through proxy (`client-update.akamai.steamstatic.com`).

## Installing Games via SteamCMD (Headless)

```bash
# 1. Install SteamCMD on macOS
mkdir -p ~/steamcmd && cd ~/steamcmd
curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_osx.tar.gz" | tar zxf -

# 2. Get app ID from store.steampowered.com/app/<id>/ or steamdb.info

# 3. Install game (must own license, use proxy in China)
cd ~/steamcmd
./steamcmd.sh +@sSteamCmdForcePlatformType windows +login <username> +app_update <app_id> validate +quit

# Anonymous login (if game allows, but many don't):
./steamcmd.sh +@sSteamCmdForcePlatformType windows +login anonymous +app_update <app_id> validate +quit
```

Key flags:
- `+@sSteamCmdForcePlatformType windows` — Force Windows platform on macOS; needed to download Windows games
- `+app_update <id> validate` — Download + verify
- Output dir: `~/Library/Application\ Support/Steam/steamapps/common/<game_name>/`

## macOS Game Compatibility

### Runs Natively
- Steam client itself
- Check store page — if Apple logo or "macOS" listed, game has native support

### Windows-Only on Apple Silicon
Use **Whisky.app** (free, recommended) or **CrossOver** (paid):
- Creates "bottles" — isolated Wine environments
- Uses Apple's Game Porting Toolkit to translate DirectX → Metal
- Supports DirectX 11 and 12 games

### Notable: CS2 Has NO macOS Support
Valve dropped macOS support when CS2 replaced CS:GO in 2023. CS2 is Windows-only. On macOS, use Whisky/CrossOver to run it.

## Checking Game Install Status

```bash
# Read manifest for app ID 730 = CS2, etc.
cat ~/"Library/Application Support/Steam/steamapps/appmanifest_<appid>.acf"

# Key fields:
# - BytesDownloaded == BytesToDownload → download complete
# - BytesStaged == BytesToStage → install complete
# - UpdateResult: 0 = success
# - SizeOnDisk: bytes on disk
# - installdir: dir name in common/

# List installed games
ls ~/"Library/Application Support/Steam/steamapps/common/"
```

## Log Analysis

Logs at `~/Library/Application Support/Steam/logs/`:

| Log | Purpose |
|-----|---------|
| `bootstrap_log.txt` | Client startup, CDN routing |
| `content_log.txt` | Download server connections |
| `cef_log.txt` | UI rendering errors |
| `webhelper_js.txt` | UI loading, login status |

```bash
# Login success?
grep "client login returned" ~/"Library/Application Support/Steam/logs/webhelper_js.txt"

# Content server failures?
grep -i "fail\|error\|success" ~/"Library/Application Support/Steam/logs/content_log.txt" | grep -v "done\|update"

# Startup status
cat ~/"Library/Application Support/Steam/logs/bootstrap_log.txt"
```

## Pitfalls

1. **CS2 install dir = "Counter-Strike Global Offensive"** — Valve kept the old CS:GO directory name. Don't be confused.
2. **Content servers blocked in China** — Login/community works via proxy, but CDN downloads may still fail. Use VPN global routing for downloads.
3. **SteamCMD on macOS** — Always use `+@sSteamCmdForcePlatformType windows` for Windows games; without it SteamCMD refuses to download.
4. **"Unsupported pixel format: -1" in cef_log.txt** — Harmless ffmpeg warning, ignore.
5. **Not all games allow anonymous login** — Use actual Steam credentials when anonymous fails.
6. **Steam login works from behind GFW** — Uses WebSocket to Dallas/LAX nodes (~200ms). Content servers (CDN) are separate and may require different proxy routing.
