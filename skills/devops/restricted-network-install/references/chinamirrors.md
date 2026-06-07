# GitHub Mirror Comparison (China Access)

## Speed Test Results (M4 Mac mini, June 2026)

All tests downloaded first 1MB of Ollama-darwin.zip (167MB).

| Mirror | Speed | HTTP Status | Notes |
|--------|-------|-------------|-------|
| `gh.ddlc.top` | **277 KB/s** | 200 | Fastest sustained |
| `ghproxy.net` | 14 KB/s | 200 | Reliable but slow |
| `gh-proxy.com` | 7.6 KB/s | 206 | Slow |
| `gh.llkk.cc` | ~0 | 301 | Redirect only |
| `gh.imsyy.top` | 0 | Timeout | Unreachable |
| `mirror.ghproxy.com` | N/A | 530 | Returns error |
| Direct GitHub | 0 | N/A | TCP RST |
| Direct ollama.com | N/A | 307 → GitHub | Redirects to same blocked URL |

## Recommendation

For files >50MB: **gh.ddlc.top** is the only practical mirror.
For small files (<1MB): any of the working mirrors will do.

## Format

```
https://gh.ddlc.top/https://github.com/<owner>/<repo>/releases/download/<tag>/<file>
https://ghproxy.net/https://github.com/<owner>/<repo>/releases/download/<tag>/<file>
```

## DIY Speed Test

```bash
# Test a mirror's speed for a specific file
TARGET="https://gh.ddlc.top/https://github.com/ollama/ollama/releases/download/v0.24.0/Ollama-darwin.zip"
curl -r 0-1048575 -s -w "Speed: %{speed_download} B/s\n" -o /dev/null \
  --connect-timeout 10 --max-time 30 "$TARGET"
```

## Go Downloads

| Resource | Mirror URL | Speed |
|----------|-----------|-------|
| Go binary (darwin/arm64) | `https://golang.google.cn/dl/go1.23.4.darwin-arm64.tar.gz` | **19 MB/s** |
| Go modules | `GOPROXY=https://goproxy.cn,direct` | Fast |

## Ollama Install Flow (Recommended Order)

1. Check if pre-built binary exists locally
2. Try `gh.ddlc.top` mirror for direct download
3. If mirror too slow (<50 KB/s): build from Go source using goproxy.cn
4. As last resort: download via V2rayU HTTP proxy on port 1087
