# Steam Log Analysis Reference

From session 2026-06-06 — CS2 installation on Mac Mini M4 behind V2rayU proxy.

## Bootstrap Log (startup)

```log
[2026-06-06 08:34:13] 4. https://client-update.akamai.steamstatic.com, /, Realm 'steamglobal', weight was 400
[2026-06-06 08:34:13] Verifying file sizes only
[2026-06-06 08:34:13] Verification complete
[2026-06-06 08:34:13] Not updating bootstrapper: No update necessary: current version 6.1
```

CDN routing check: akamai.steamstatic.com succeeded through proxy. No bootstrap update needed.

## Content Log (download servers failing in China)

```log
[2026-06-04 18:04:04] ContentServerDirectoryService::BYieldingGetServersForSteamPipe failed (Transport Request Not Sent / Result No Connection)
[2026-06-04 18:04:04] Failed to get list of download sources
[2026-06-04 17:14:09] HTTPS (SteamCache,278) - cache5-lax1.steamcontent.com (162.254.195.14:443 / 127.0.0.1:10809, host: cache5-lax1.steamcontent.com): Closing connection
```

- `BYieldingGetServersForSteamPipe failed` = CDN directory server unreachable (blocked in China)
- `cacheN-lax1.steamcontent.com / 127.0.0.1:10809` = Some connections DID go through proxy (port 10809 = different proxy port)
- Login succeeded through Dallas node at ~196ms even when CDN failed

## Web Helper JS (login confirmation)

```js
[2026-06-04 13:57:40] SteamUI: INFO: client login returned 1 (Success)
```

`1` means success. Any other value means login failed.

## CEF Log (harmless noise)

```log
[31063:259:0606/083414.662754:ERROR:unexportable_key_mac.mm(348)] Unexportable keys unavailable because keychain-access-group entitlement missing
[0606/083414.671835:ERROR:check.cc(376)] Check failed: false. NOTREACHED
[3627:49931:0604/172326.238086:ERROR:ffmpeg_common.cc(959)] Unsupported pixel format: -1
```

All three are harmless Chromium/CEF internal warnings:
- Keychain entitlement missing — Steam Helper doesn't declare the expected keychain group
- NOTREACHED check — DCHECK assertion in Chromium's official build
- ffmpeg pixel format — Video decoding fallback issue, doesn't affect gameplay

## App Manifest Example (appmanifest_730.acf for CS2)

```ini
"AppState" {
  "appid"             "730"
  "name"              "Counter-Strike 2"
  "installdir"        "Counter-Strike Global Offensive"    # !!! Old CS:GO name kept
  "SizeOnDisk"        "60351000018"                        # 60.3 GB
  "BytesDownloaded"   "51565971664"                        # 51.5 GB download
  "BytesStaged"       "60351000018"                        # 60.3 GB staged
  "UpdateResult"      "0"                                  # 0 = success
  "LastPlayed"        "0"                                  # never played
  "UserConfig" { "language" "schinese" }
}
```

## Steam Process List (macOS)

When Steam is running, look for:
- `steam_osx` — main process
- `Steam Helper --type=gpu-process` — GPU renderer
- `Steam Helper --type=renderer` — CEF web renderer (locale = zh-CN)
- `Steam Helper --type=utility` — network service, storage service
- `Steam Helper` (crashpad-handler) — error reporting
- `ipcserver` — Steam IPC daemon

## Whisky.app

Located at `/Applications/Whisky.app`. Free Wine-based compatibility layer for running Windows games on Apple Silicon. Uses Apple's Game Porting Toolkit for DirectX→Metal translation.
