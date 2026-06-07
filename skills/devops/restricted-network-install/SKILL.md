---
name: restricted-network-install
description: "Install developer tools in network-restricted environments (China firewall, corporate proxy, slow VPN). Covers mirrors, quarantine bypass, proxy configuration, and source builds."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [network, proxy, china, mirror, install, macos, go, github]
    related_skills: [systematic-debugging, llama-cpp, hermes-agent]
---

# Restricted-Network Install

## Overview

Standard `curl | sh` and `brew install` patterns fail in environments where GitHub, Google, and other global CDNs are slow or unreachable. This skill provides workarounds and mirroring strategies.

**Core principle:** Before attempting any download, identify the network constraint (DNS block, throttled bandwidth, HTTP2 framing errors, TCP RST) and pick the right bypass.

---

## Diagnosing the Constraint

| Symptom | Likely Cause | Bypass |
|---------|-------------|--------|
| `curl: (56) Recv failure: Operation timed out` | Global CDN unreachable | GitHub mirror |
| `curl: (16) Error in the HTTP2 framing layer` | Proxy/protocol mismatch | Use `--http1.1` flag |
| `brew: SIGTERM in download_queue.rb` | Brew downloads timing out | Set `HOMEBREW_BOTTLE_DOMAIN` |
| `xattr: com.apple.quarantine` blocks app | macOS Gatekeeper | Remove quarantine |
| Download starts, 0.1% → stalls | Bandwidth throttled | Find faster mirror or parallel download |
| `go install` times out | Go modules unreachable | Set `GOPROXY` |
| `git clone` hangs | GitHub TCP RST | Use Gitee/ghproxy |

---

## macOS Specifics

### Remove Quarantine from Untrusted Apps

```bash
# Check if quarantined
xattr -l /Applications/SomeApp.app

# Remove quarantine (may work without sudo if user owns file)
xattr -d com.apple.quarantine /Applications/SomeApp.app

# Also clean embedded binaries
xattr -d com.apple.quarantine /Applications/SomeApp.app/Contents/MacOS/binary
```

Note: `com.apple.provenance` is harmless — no need to remove it.

### Set Up V2rayU as System Proxy

1. Install V2rayU, remove quarantine as above
2. Start core via launchctl:
   ```bash
   launchctl kickstart gui/501/yanue.v2rayu.v2ray-core
   ```
3. Proxy ports: SOCKS5 on `127.0.0.1:1080`, HTTP on `127.0.0.1:1087`
4. Set env vars for terminal:
   ```bash
   export http_proxy=http://127.0.0.1:1087
   export https_proxy=http://127.0.0.1:1087
   export all_proxy=socks5h://127.0.0.1:1080
   ```

---

## GitHub Mirror Strategy

### Speed-Test Mirrors

Test the first 1MB to find the fastest mirror:

```bash
for url in \
  "https://ghproxy.net/..." \
  "https://gh.ddlc.top/..."; do
  curl -r 0-1048575 -s -w "Speed: %{speed_download} B/s\n" -o /dev/null \
    --connect-timeout 10 --max-time 20 "$url"
done
```

### Known Working Mirrors (China)

| Mirror | Typical Speed | Notes |
|--------|---------------|-------|
| `gh.ddlc.top` | 100-300 KB/s | Fastest for large files |
| `ghproxy.net` | 5-50 KB/s | Reliable but slow |
| `mirror.ghproxy.com` | Variable | Sometimes gives HTTP 530 |

URL format: `https://<mirror>/https://github.com/<owner>/<repo>/releases/download/<tag>/<file>`

---

## Go Toolchain

### Download Go Binary

```bash
# Use Google China CDN (very fast, 3s for 70MB)
curl -L -o /tmp/go.tar.gz \
  "https://golang.google.cn/dl/go1.23.4.darwin-arm64.tar.gz"

# Extract
mkdir -p ~/.local/go
tar -C ~/.local -xzf /tmp/go.tar.gz
export PATH="$HOME/.local/go/bin:$PATH"
```

### Go Module Proxy

```bash
export GOPROXY=https://goproxy.cn,direct
export GO111MODULE=on
```

### Build Ollama from Source

```bash
export GOPROXY=https://goproxy.cn,direct
export PATH="$HOME/.local/go/bin:$PATH"
git clone --depth 1 https://gitee.com/mirrors/ollama.git /tmp/ollama-source
cd /tmp/ollama-source && go generate && go build .
```

---

## Homebrew Mirror

```bash
# Use USTC mirror for Homebrew bottles
export HOMEBREW_BOTTLE_DOMAIN=https://mirrors.ustc.edu.cn/homebrew-bottles
export HOMEBREW_API_DOMAIN=https://mirrors.ustc.edu.cn/homebrew-api

# Or Tsinghua
export HOMEBREW_BOTTLE_DOMAIN=https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles
```

Note: Only works for formulas with prebuilt bottles. If "Bottle missing" appears, the formula must build from source.

---

## Download Ollama

### Option A: Pre-built from GitHub mirror (preferred)

```bash
curl -L -o /tmp/Ollama-darwin.zip \
  "https://gh.ddlc.top/https://github.com/ollama/ollama/releases/download/v0.24.0/Ollama-darwin.zip"
```

### Option B: Build from Go source (if mirror slow)

```bash
# Install Go from golang.google.cn first
export GOPROXY=https://goproxy.cn,direct
git clone --depth 1 https://gitee.com/mirrors/ollama.git /tmp/ollama
cd /tmp/ollama
go generate
go build .
```

### Option C: Use existing cache

Check `/tmp/` and `~/Library/Caches/Homebrew/downloads/` for partial downloads, then resume with `curl -C -`.

---

## Known Pitfalls

- **HTTP2 framing errors** through proxy → add `--http1.1` to curl
- **ghproxy returns 530** → switch to gh.ddlc.top or direct raw.githubusercontent.com
- **Brew SIGTERM** → brew's download queue is stuck. Kill stale processes: `pkill -f brew` and retry with a mirror
- **Speed test lies** — first 1MB might be cached; sustained speed can be 10x lower. Test with larger ranges.
- **V2rayU core dies silently** — check with `ps aux | grep v2ray` and `launchctl list | grep v2ray`

## Reference Files

- `references/v2rayu-macos.md` — V2rayU config structure, proxy ports, troubleshooting
- `references/chinamirrors.md` — GitHub mirror speed comparison, Go download URLs, recommended install order
