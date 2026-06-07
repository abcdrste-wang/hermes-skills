---
name: cloudflare-bypass-web-scraping
description: Strategies and tools for web scraping behind Cloudflare WAF/Turnstile on macOS — curl_cffi (TLS fingerprint), playwright stealth (browser automation), nodriver, zendriver. Covers Python version requirements, proxy routing, and debugging headless browser detection.
---

# Cloudflare Bypass / Anti-Detection Web Scraping

## Overview

Cloudflare WAF (Turnstile, JS challenge, 5-second shield) blocks standard `requests`/`httpx` by detecting non-browser TLS fingerprints and missing browser behaviors. This skill documents layered bypass strategies tested on macOS (Apple Silicon).

**Layered approach** (try in order):
1. **TLS-level**: `curl_cffi` — impersonates real browser TLS handshake (JA3/JA4)
2. **Browser-level**: `playwright` / `nodriver` / `zendriver` — full headless browser with stealth patches
3. **C++-level**: Camoufox (Firefox fork) — deep fingerprint obfuscation (not yet tested)

---

## Layer 1: curl_cffi (TLS Fingerprint Spoofing)

### Installation

```bash
# Python 3.9+ (works on system Python)
pip3 install curl_cffi
```

### Usage

```python
from curl_cffi import requests

# Use a real browser impersonation
r = requests.get("https://example.com", impersonate="chrome131", timeout=15)
```

**Available impersonations** (list via `BrowserType`):
- Chrome: `chrome99`, `chrome101`, `chrome104`, `chrome107`, `chrome110`, `chrome116`, `chrome119`, `chrome120`, `chrome123`, `chrome124`, `chrome131`, `chrome133a`, `chrome136`
- Edge: `edge99`, `edge101`
- Safari: `safari15_3`, `safari15_5`, `safari17_0`, `safari18_0`, `safari153`, `safari155`, `safari170`, `safari180`, `safari184`, `safari260`
- Firefox: `firefox133`, `firefox135`
- Tor: `tor145`
- Android: `chrome99_android`, `chrome131_android`
- iOS: `safari17_2_ios`, `safari18_0_ios`, `safari180_ios`, `safari184_ios`, `safari260_ios`

### Limitations

- Works against basic Cloudflare WAF (5-second shield, JS challenge)
- **Does NOT work against Turnstile** (Cloudflare's invisible CAPTCHA) — GSMArena uses Turnstile, curl_cffi gets a 1.9KB placeholder page
- Some sites (e.g., GSMArena) time out connections through certain proxy IPs — try different proxy nodes
- Notebookcheck.net passes with curl_cffi (no Turnstile)

### Session Support

```python
s = requests.Session()
r = s.get("https://example.com", impersonate="chrome131")
```

### Proxy Support

```python
r = requests.get("https://example.com", impersonate="chrome131",
                 proxies={"https": "http://127.0.0.1:1087"})
```

---

## Layer 2: Browser Automation (Playwright)

### Installation (Python 3.11+)

```bash
# Use brew's Python 3.11+ (system Python 3.9 doesn't support nodriver)
export http_proxy=http://127.0.0.1:1087
export https_proxy=http://127.0.0.1:1087

/opt/homebrew/bin/python3.11 -m pip install playwright playwright-stealth
/opt/homebrew/bin/python3.11 -m playwright install chromium
```

### Python Version Requirements

| Tool | Min Python | Notes |
|------|-----------|-------|
| `curl_cffi` | 3.9 | Works with system `/usr/bin/python3` |
| `playwright` | 3.8+ | Works with brew Python 3.11 |
| `nodriver` | 3.10+ | Needs `str | Path` syntax (3.10+) |
| `zendriver` | 3.10+ | Similar requirements to nodriver |

### playwright-stealth API

**Version 2.0.3 API:**
```python
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            locale="en-US",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # CORRECT API: apply_stealth_async / apply_stealth_sync
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # NOT: Stealth(page) — TypeError: takes 1 positional arg but 2
        # NOT: context.add_init_script(stealth.stealth_js()) — no such method
        
        await page.goto("https://target.com", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(8)  # wait for Turnstile auto-resolution
        
        content = await page.content()
        # ...
        await browser.close()
```

### Turnstile Handling

Even with playwright-stealth, **headless Chrome is detected by Turnstile** (GSMArena consistently shows "GSMArena Turnstile check" title and never resolves). The stealth patches (navigator.webdriver, plugins, languages, chrome.runtime) are insufficient against invisible Turnstile when headless.

**Known working approaches (untested in this session):**
1. Turnstile-Solver (patchright-based) — ★821 on GitHub
2. zendriver (Puppeteer-core fork) — ★1309, may have better stealth
3. Use a real display (not headless) — requires Xvfb or macOS accessibility
4. nodriver — may work better but had Chrome 149 connection issues

### nodriver Pitfalls

- **Chrome compatibility**: `nodriver` launches Chrome via subprocess and connects via CDP. If Chrome 149 is installed but nodriver can't connect, try:
  - Passing `no_sandbox=True` (for root)
  - Specifying `browser_executable_path` explicitly
  - Check if chromedriver auto-download is needed
- **Headless mode**: Pass `--headless=new` in `browser_args`
- **Event loop**: nodriver uses asyncio; event loop must not be closed before cleanup

---

## Layer 3: C++-level (Camoufox)

Not yet tested. Camoufox is a Firefox fork with C++-level fingerprint obfuscation (★8998). Has a REST API and Docker support.

---

## Testing Strategy

1. **First test with curl_cffi** against the target — fast, no browser needed
2. **If Turnstile blocked**, try browser automation with stealth
3. **If still blocked**, screenshot the page to see what's happening (what kind of challenge)
4. **For screenshots when vision API is down**: save to `/tmp/` and send to user via `send_message` with `MEDIA:`

```python
# Screenshot debug pattern
await page.screenshot(path="/tmp/cf_debug.png")
# Then share with user:
# send_message(target="...", message="MEDIA:/tmp/cf_debug.png")
```

---

## Environment-Specific Notes

### Proxy in China (V2rayU)

On this Mac Mini M4 (China GFW):
- V2rayU proxy: HTTP `127.0.0.1:1087`, SOCKS5 `127.0.0.1:1080`
- Set `http_proxy`/`https_proxy` for terminal commands accessing international sites
- Use `-i https://pypi.tuna.tsinghua.edu.cn/simple` for pip without proxy
- **GSMArena connections time out through proxy** — try different V2rayU nodes or direct connection
- Some international CDNs (notebookcheck) work fine through proxy

### macOS (Apple Silicon)

- System Python is 3.9 — good for curl_cffi but not for nodriver/zendriver
- brew's `/opt/homebrew/bin/python3.11` for newer Python needs
- Chrome is at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Playwright can use system Chrome via `executable_path` or its bundled Chromium

---

## E-commerce Scraping (Price Comparison)

This skill also covers **e-commerce platform scraping** — a common subclass of web-scraping that adds login, cookie persistence, and session management on top of anti-detection.

**Pattern**: Agent delegates to a standalone Playwright script → manages cookies → returns formatted comparison table.

### Platform-specific notes

| Platform | Status | Main Challenge |\n|----------|--------|---------------|\n| 淘宝 (Taobao) | ✅ Works | Cookie 7-30 day rotation, CSS structure changes |\n| 京东 (JD.com) | ⚠️ Needs `area=1` URL parameter | Region selector overlay blocks results even with valid cookies |\n| 拼多多 (Pinduoduo) | ❌ Not supported | Custom TCP protocol, non-HTTP, Playwright can't simulate |

### Architecture

```
Agent/LM ──call──▶ Python script ──Playwright──▶ Chromium (headless/GUI)
                      │
                      ├── Cookie persistence (~/.hermes/pricer_cookies/)
                      ├── Page parsing (CSS selectors with fallbacks)
                      └── Formatted output (comparison table)
```

### Key design decisions

1. **Dual mode**: `login` = GUI (QR code scan required), `search` = headless (cookie reuse)
2. **Separate cookie stores**: each platform independently authenticated and expired
3. **Multi-level CSS fallback**: e-commerce sites change structure frequently; provide 2-3 selector variants per field
4. **Full-info extraction**: item name + price + shop + sales + link → average price comparison

### Cookie persistence strategy

- Save cookies via `context.cookies()` → JSON file after manual login
- Load via `context.add_cookies()` before each headless search
- Cookie file location: `~/.hermes/pricer_cookies/{platform}.json`
- On cookie expiry: re-run `login` command (manual QR scan)

### Interactive login → headless search workflow

E-commerce scraping follows a **two-phase pattern** that is generalizable to any site requiring authentication:

```
Phase 1: login (GUI, one-time)
  Agent runs script with headless=False
  → Chromium window pops up
  → User scans QR code / enters credentials manually
  → Script saves cookies to JSON
  → Browser closes

Phase 2: search (headless, repeatable)
  Agent runs script with headless=True
  → Script loads saved cookies
  → Runs search against platform
  → Returns formatted results
  → Browser closes
```

**Process management in Hermes** — because `login` needs GUI interaction and can take 60-120s:

1. Launch with `terminal(background=True)` — foreground timeout will kill the script before the user finishes scanning
2. Use `python3 -u` flag to disable stdout buffering; without it, background process output may not show up in `process(log=...)` for many seconds
3. Poll with `process(action='log')` to read output and confirm login is ready
4. Check with `ps aux | grep chromium` to verify browser window actually launched
5. The script's `_wait_for_login()` function uses polling on page DOM; total timeout of ~120s is standard for QR-code login

**Background process stdout pitfalls**:
- Python buffers stdout aggressively when not connected to a TTY (which `background=true` isn't)
- Always use `python3 -u` or set `PYTHONUNBUFFERED=1` for any long-lived interactive script
- Without this, `process(action='log')` returns empty output even though the script is running fine
- Confirmation: `ps aux | grep chromium` will show the browser process even when stdout is empty

## Reference Files

- `references/ecommerce-price-comparison.md` — full Taobao + JD comparison tool implementation notes, anti-detection tricks, and CSS selector strategies
- `references/tool-comparison.md` — detailed comparison of curl_cffi vs nodriver vs playwright vs zendriver vs Camoufox
- `references/turnstile-solver-github.md` — Turnstile-Solver project details (★821, patchright-based)
- `references/hermes-cf-bypass.md` — Hermes-specific cf-bypass skill (★6, uses curl_cffi monkey-patch)
- `references/ecommerce-real-session-june-2026.md` — real Taobao+JD login session results (June 2026), JD region selector fix, verified working search output
- `references/background-process-stdout-buffering.md` — Python stdout buffering when running scripts with `terminal(background=True)` and why `python3 -u` is required
