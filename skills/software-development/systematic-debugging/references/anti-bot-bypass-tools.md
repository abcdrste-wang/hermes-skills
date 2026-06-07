# Anti-Bot / Cloudflare Bypass Tool Landscape

> Condensed reference: which tool for which level of blocking.
> Last updated: 2026-06-06

## Decision Flow

```
Try curl / wget / web_extract first
  ├── Works? → Done.
  └── Blocked (Cloudflare/403/challenge page)?
       ├── Is it just TLS fingerprint? → try curl_cffi / httpcloak
       ├── JS challenge (cf_challenge) → try cloudscraper / nodriver
       ├── Turnstile CAPTCHA → try Turnstile-Solver or capsolver
       └── Aggressive WAF (datacenter IP blocked) → camofox-browser / residential proxy
```

## Tool Reference

### Level 1: Request-level (lightest, pip install)

| Tool | Stars | What it does | When to use | Install |
|------|-------|-------------|-------------|---------|
| **curl_cffi** | ★5,755 | Python binding for curl-impersonate. Spoofs Chrome TLS/JA3/JA4 fingerprint at the libcurl C level. | Site blocks Python's httpx/requests but works in a real browser. Good first try for TLS-based blocking. | `pip install curl_cffi` |
| **cloudscraper** | ★6,573 | Extends requests.Session with JS challenge solving (via node.js subprocess). | JS challenge (the spinning cloudflare page) but NOT Turnstile. Older, less maintained. | `pip install cloudscraper` |
| **httpcloak** | ★1,083 | Full transport layer emulation: TLS, HTTP/2 frames, QUIC, Sec-Fetch-* headers. Available in Python/Go/JS. | Sites with sophisticated fingerprinting beyond just TLS (header ordering, HTTP/2 settings). | `pip install httpcloak` |

### Level 2: Browser automation (heavier, needs Playwright/Chrome)

| Tool | Stars | What it does | When to use | Install |
|------|-------|-------------|-------------|---------|
| **nodriver** | ★4,318 | Successor to undetected-chromedriver. Async-first, auto-patches Chrome to avoid detection. | JS-heavy sites, single-page apps, sites that check navigator/webdriver properties. | `pip install nodriver` |
| **zendriver** | ★1,309 | nodriver fork with Docker support, active maintenance. | Same as nodriver but want Docker deployment. | `pip install zendriver` |
| **Turnstile-Solver** | ★821 | Dedicated Cloudflare Turnstile solver using patchright (Playwright fork). HTTP API mode. | Sites protected by Turnstile CAPTCHA (click-the-checkbox style). | `git clone` + `pip install -r requirements.txt` |

### Level 3: C++ anti-detection (heaviest, most effective)

| Tool | Stars | What it does | When to use | Install |
|------|-------|-------------|-------------|---------|
| **Camoufox** | ★8,998 | Firefox fork with C++-level fingerprint spoofing. Patches navigator, WebGL, AudioContext, screen geometry BEFORE JS runs. | Aggressive WAF (DataDome, Imperva, Kasada). Sites that detect headless browsers even with stealth plugins. | `pip install camoufox` or download binary |
| **camofox-browser** | ★6,395 | Wraps Camoufox in a REST API (Docker/standalone). Accessibility snapshot format, element refs for clicking. | AI agents that need to browse the real web. Drop-in replacement for Playwright/Puppeteer. | `npx @askjo/camofox-browser` or `git clone` + `npm install` |

### Level 4: Proxy + fingerprint (production)

| Approach | Description |
|----------|-------------|
| **Residential proxies** (BrightData, Oxylabs, Smartproxy) | Route through real home IPs. Essential when datacenter IPs are blocked regardless of browser fingerprint. |
| **Browserbase / stealth browser APIs** | Managed headless browsers with residential proxy pools built in. | 

## Signal Detection: How to tell what level of blocking you're hitting

Check the response body when a request fails:

```python
import httpx
r = httpx.get("https://target.com")
print(r.status_code, r.text[:500])
```

| Signal | Blocking Level | Tool Choice |
|--------|---------------|-------------|
| `HTTP 403` + `<title>Just a moment...</title>` + JS challenge script | JS Challenge (IUAM) | cloudscraper, nodriver |
| `HTTP 403` + `cf-error-code` in JSON | WAF rule, TLS fingerprint | curl_cffi, httpcloak |
| `HTTP 403` + Turnstile widget HTML (`cf-turnstile`) | Turnstile CAPTCHA | Turnstile-Solver, capsolver |
| `HTTP 200` + "we detected unusual traffic" | Behavioral/browser detection | camofox-browser, residential proxy |
| Timeout / connection reset | IP-level block (datacenter blacklist) | residential proxy required |

## Python Quick Start - curl_cffi (for Hermes agents)

```python
from curl_cffi import requests

# Chrome 130 fingerprint
r = requests.get("https://target.com", impersonate="chrome130")
print(r.status_code, r.text[:200])
```

Available impersonate strings: `chrome99`, `chrome110`, `chrome116`, `chrome120`, `chrome123`, `chrome124`, `chrome130`, `safari15_5`, `safari17_0`

## Python Quick Start - nodriver

```python
import nodriver as uc

async def main():
    browser = await uc.start()
    page = await browser.get("https://target.com")
    text = await page.evaluate("document.body.innerText")
    print(text[:500])
    await browser.stop()

uc.loop().run_until_complete(main())
```

## Hermes-Specific: curl_cffi monkey-patch for httpx

When Hermes' own httpx client gets blocked by Cloudflare (e.g., OAuth endpoints, certain websites):

```python
# Patch httpx.Client to use curl_cffi for specific domains
from curl_cffi import requests as curl_requests
import httpx

class CFFallbackTransport(httpx.BaseTransport):
    def __init__(self, impersonate="chrome130"):
        self.impersonate = impersonate
    
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        kwargs = {
            "impersonate": self.impersonate,
            "headers": dict(request.headers),
        }
        if request.content:
            kwargs["data"] = request.content
        r = curl_requests.request(
            method=request.method,
            url=str(request.url),
            **kwargs
        )
        return httpx.Response(r.status_code, headers=r.headers, content=r.content)

# Usage:
client = httpx.Client(transport=CFFallbackTransport())
r = client.get("https://target.com")
```

## References

- curl_cffi: https://github.com/lexiforest/curl_cffi
- cloudscraper: https://github.com/VeNoMouS/cloudscraper
- nodriver: https://github.com/ultrafunkamsterdam/nodriver
- zendriver: https://github.com/cdpdriver/zendriver
- Turnstile-Solver: https://github.com/Theyka/Turnstile-Solver
- Camoufox: https://github.com/daijro/camoufox
- camofox-browser: https://github.com/jo-inc/camofox-browser
- httpcloak: https://httpcloak.dev
- hermes-cf-bypass: https://github.com/0xNyk/hermes-cf-bypass
