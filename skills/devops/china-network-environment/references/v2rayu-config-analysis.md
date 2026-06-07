# V2rayU Server Config Analysis

## Plist Structure
- Location: `~/Library/Preferences/net.yanue.V2rayU.plist`
- Format: Binary plist
- Server list key: `v2rayServerList` (array of `config.<UUID>` keys)
- Current server: `v2rayCurrentServerName`
- Mode: `runMode` (pac, global, manual)
- Enabled: `v2rayTurnOn` (bool)
- Subscription list: `v2raySubList` (array of `subscribe.<UUID>` keys)

## Decoding Server Configs
Each `config.<UUID>` value is a binary plist containing:
- `name`: Server name (can be empty/unnamed)
- `address`: Server IP/hostname
- `port`: Port number
- `protocol`: VMess, VLESS, Shadowsocks, etc.
- `streamSettings.network`: tcp, ws, kcp, quic, grpc
- `streamSettings.wsSettings.headers.host`: Host header for WebSocket
- `streamSettings.tlsSettings.serverName`: TLS SNI

## Node Speed Benchmarking
Benchmark a node by:
1. Extracting its address from plist
2. Testing latency: `ping -c 3 <address>`
3. Testing proxy throughput via the V2rayU SOCKS5/HTTP proxy
