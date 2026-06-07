# V2rayU macOS Setup Reference

## Config Structure (VLESS + WebSocket + TLS)

The V2rayU config lives at `~/.V2rayU/config.json`. Key structure:

```json
{
  "inbounds": [
    {"port": "1080", "protocol": "socks", "listen": "127.0.0.1"},
    {"port": "1087", "protocol": "http", "listen": "127.0.0.1"}
  ],
  "outbounds": [{
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "<server_ip>",
        "port": 8443,
        "users": [{"id": "<uuid>", "encryption": "none"}]
      }]
    },
    "streamSettings": {
      "network": "ws",
      "security": "tls",
      "wsSettings": {
        "headers": {"host": "<sni_host>"},
        "path": "/"
      },
      "tlsSettings": {
        "serverName": "<sni_host>",
        "allowInsecure": true,
        "fingerprint": "chrome"
      }
    }
  }]
}
```

## LaunchAgent

Managed by `~/Library/LaunchAgents/yanue.v2rayu.v2ray-core.plist`.

- Working directory: `~/.V2rayU/`
- Core binary: `./v2ray-core/v2ray` (or v2ray-arm64 on Apple Silicon)
- Log: `~/.V2rayU/v2ray-core.log`

## Important: The bundled v2ray-core is actually Xray

Despite the name, the bundled binary at `~/.V2rayU/v2ray-core/v2ray` identifies as "Xray 25.10.15" at startup. This is fine — Xray is the actively maintained fork of v2ray-core and fully compatible.

## Proxy Ports

| Protocol | Port | Usage |
|----------|------|-------|
| SOCKS5 | 1080 | Terminal: `export all_proxy=socks5h://127.0.0.1:1080` |
| HTTP | 1087 | Terminal: `export https_proxy=http://127.0.0.1:1087` |

## Troubleshooting

### Core not running
```bash
ps aux | grep v2ray
launchctl list | grep v2ray
```

### Restart core
```bash
launchctl kickstart gui/501/yanue.v2rayu.v2ray-core
```

### Logs
```bash
tail -f ~/.V2rayU/v2ray-core.log
```

Look for:
- "Xray ... started" — core is up
- "listening TCP on 127.0.0.1:1080" — proxy port ready
- "tunneling request to ... via ..." — connection flowing through remote server
