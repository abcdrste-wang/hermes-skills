---
name: china-network-environment
description: Working with Chinese network restrictions — domestic mirrors, proxy setup, Go/HuggingFace/GitHub mirrors, and installing software without direct VPN access. Covers configuration for terminal, Homebrew, Go modules, and model downloads.
---

# China Network Environment

Skills for working within China's internet environment. Use this when the user's machine is in mainland China and cannot directly reach GitHub, HuggingFace, Ollama registry, or other international services.

## General Approach (User Preference)

**Do NOT blindly try random approaches.** Before attempting any download or network operation:
1. Search for the correct solution first (web search, browser, or ask)
2. Check if domestic mirrors exist for the service
3. Only then attempt the operation
4. If it fails, search for the specific error, don't just try random workarounds

The user explicitly corrected this workflow: *"你可以去网上搜一下解决方案吗？瞎试什么啊"* — always research before executing.

## Proxy Bypass Pattern: When Proxy Slows Things Down

**Counterintuitive but common:** Some international services (GitHub, Ollama registry, Docker Hub) are actually **reachable directly from China** — the proxy is slower for large binary downloads because it adds latency and bandwidth limits.

**New finding:** Some international websites (e.g., GSMArena) TIME OUT through common V2rayU proxy nodes — try different proxy nodes or direct connection if proxy connections time out with errors like `curl: (28) Connection timed out`.

### The `no_proxy=*` technique

Bypass the proxy entirely for specific commands:

```bash
# Method 1: Set no_proxy environment
no_proxy=* http_proxy= https_proxy= ollama pull qwen2.5:7b

# Method 2: For curl, use --noproxy
curl -L --noproxy "*" -o file.zip "https://hf-mirror.com/..."

# Method 3: Unset proxy variables inline
(unset http_proxy https_proxy; ollama pull qwen2.5:7b)
```

**When to use `no_proxy=*`:**
- Ollama model pulls (`registry.ollama.ai`) — often 1-8 MB/s direct vs 200-500 KB/s through proxy
- HuggingFace downloads via `hf-mirror.com` — this is a Chinese mirror, should not go through proxy
- GitHub releases via `gh.ddlc.top` — also a Chinese mirror
- **Qwen/Alibaba models** — always try without proxy first (domestic company, fast direct)
- Any DDL (direct download link) that originates from a domestic CDN

**Signs the proxy is the bottleneck:**
- Download starts fast (>2 MB/s) then drops to <500 KB/s
- Download stalls at a certain percentage and won't progress
- Tool reports "speed too slow" errors

**Signs the proxy IS needed:**
- Connection times out without proxy
- DNS resolution fails
- HTTP 4xx/5xx errors without proxy but 200 with proxy

## Domestic Mirror Reference

### GitHub Release Mirrors (for large binaries)
| Mirror | Typical Speed | Notes |
|--------|--------------|-------|
| `gh.ddlc.top` | 200-500 KB/s | Fastest tested, use `curl -L -o file "https://gh.ddlc.top/https://github.com/.../releases/download/..."` |
| `ghproxy.net` | 10-30 KB/s | Reliable but slower |
| `gh-proxy.com` | 5-10 KB/s | Partial content supported |

### HuggingFace
- **Mirror**: `hf-mirror.com`
- Speed: ~28 KB/s (slow but works without proxy)
- Usage: Replace `huggingface.co` with `hf-mirror.com` in URLs

### Go Language
- **Download site**: `golang.google.cn` — very fast (19 MB/s+)
- **Go module proxy**: `GOPROXY=https://goproxy.cn,direct`
- Install: Download tarball from `golang.google.cn/dl/`, extract to `~/.local/go/`, add to `PATH`

### Ollama Model Mirror Strategy
- **Qwen series (千问)** from Alibaba: **Do NOT need proxy/VPN** — `ollama pull qwen*` works directly in China
- Speed: 2-8 MB/s for Qwen models
- Other models may need proxy or alternative download method

### PyPI (Python Packages)

**Tsinghua mirror** (most complete):
```bash
pip install <package> -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

**Gotchas:**
- Some packages (e.g., `nodriver`) may not be on the mirror yet — fall back to proxy to default PyPI
- Large `.whl` files (>2MB) can timeout on Tsinghua mirror too — use `--resume-retries 3` or split downloads
- If mirror returns "No matching distribution found", the package may not be synced yet → use proxy to default PyPI: `export http_proxy=... && pip install <package>`

### Homebrew
- **Bottle mirror**: `HOMEBREW_BOTTLE_DOMAIN=https://mirrors.ustc.edu.cn/homebrew-bottles`
- **API mirror**: `HOMEBREW_API_DOMAIN=https://mirrors.ustc.edu.cn/homebrew-api`
- **Note**: Some formulae have no bottle (fall back to source build which may fail)

## Proxy Configuration

### V2rayU (macOS GUI Proxy Client)
- **Config location**: `~/Library/Preferences/net.yanue.V2rayU.plist` (binary plist)
- **Running core**: `~/.V2rayU/` directory
- **Core binary**: `~/.V2rayU/v2ray-core/v2ray` (or v2ray-arm64)
- **Config**: `~/.V2rayU/config.json`
- **Log**: `~/.V2rayU/v2ray-core.log`
- **Ports**: SOCKS5 on 1080, HTTP on 1087
- **System proxy**: NOT enabled by default; core runs independently
- **Node switching**: See `references/v2rayu-node-switching.md` for programmatic and manual switching between subscription nodes

### Terminal Proxy Environment Variables
```bash
# HTTP proxy (via V2rayU)
export http_proxy=http://127.0.0.1:1087
export https_proxy=http://127.0.0.1:1087
export HTTP_PROXY=http://127.0.0.1:1087
export HTTPS_PROXY=http://127.0.0.1:1087

# SOCKS5 proxy (via V2rayU)
export all_proxy=socks5h://127.0.0.1:1080

# Unset all proxy
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
```

### macOS Proxy Commands
```bash
# Check system proxy settings
networksetup -getwebproxy Wi-Fi
networksetup -getsocksfirewallproxy Wi-Fi
scutil --proxy
```

### Steam in China

Steam has a **split network architecture** — login/WebSocket connections (via CM servers like `cmp1-dfw2.steamserver.net`) work from China behind a proxy, but game **content download servers** (CDN) are blocked by the GFW. See `references/steam-china-network.md` for full diagnostics: log file locations, the "login OK but downloads fail" pattern, and workarounds including V2rayU proxy setup and diagnostic script.

### V2rayU Plist Decoding
Server configs are stored as binary plist data under keys `config.<UUID>` in the preferences plist. Use Python to decode:
```python
import plistlib
with open('net.yanue.V2rayU.plist', 'rb') as f:
    plist = plistlib.load(f)
for key in plist.get('v2rayServerList', []):
    data = plist.get(key)
    if data and key.startswith('config.'):
        cfg = plistlib.loads(data)
        # cfg dict has: name, address, port, protocol, streamSettings, etc.
```

## Installing Ollama on macOS (M4/Apple Silicon) Without Brew

When `brew install ollama` fails in China, build from source:

```bash
# 1. Install Go from domestic mirror
curl -L -o /tmp/go.tar.gz "https://golang.google.cn/dl/go1.23.4.darwin-arm64.tar.gz"
mkdir -p ~/.local/go && tar -C ~/.local -xzf /tmp/go.tar.gz
export PATH="$HOME/.local/go/bin:$PATH"

# 2. Clone from Gitee mirror (GitHub mirror)
git clone --depth 1 https://gitee.com/mirrors/ollama.git /tmp/ollama-source

# 3. Build with Go proxy
cd /tmp/ollama-source
export GOPROXY=https://goproxy.cn,direct
go build -o ~/.local/bin/ollama .

# 4. Run
~/.local/bin/ollama serve
```

Ollama detects Apple M4 Metal automatically with ~11.8 GiB VRAM available.

## Model Size Estimation for Apple Silicon Macs
- 7B model (Q4): ~4-6 GB — fits comfortably on 16GB M4
- 8-9B model (Q4): ~5-7 GB — fits on 16GB M4 with headroom
- 10B+ model: check carefully
- Available VRAM: typically ~75% of total RAM (11.8 GiB on 16GB M4)
