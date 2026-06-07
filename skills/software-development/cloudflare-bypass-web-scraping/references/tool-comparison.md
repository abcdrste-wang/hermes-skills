# Cloudflare Bypass Tool Comparison

Tested on: Mac Mini M4 (macOS 26.5.1), China GFW behind V2rayU proxy
Date: June 2026

## Layer 1: Request-level (TLS Fingerprint)

### curl_cffi ★6573
- **Python**: 3.9+
- **Install**: `pip3 install curl_cffi`
- **Status**: ✅ Working (v0.13.0 on system Python 3.9, v0.15.0 on brew Python 3.11)
- **Passes**: notebookcheck.net (no Turnstile)
- **Fails**: gsmarena.com (Turnstile — gets 1.9KB placeholder page)
- **Notes**: Connection to gsmarena times out through V2rayU proxy (curl error 28). Try different proxy nodes.

### httpcloak ★1083
- **Not tested**

## Layer 2: Browser-level

### playwright 1.60.0 + playwright-stealth 2.0.3
- **Python**: 3.8+
- **Install**: `/opt/homebrew/bin/python3.11 -m pip install playwright playwright-stealth`
- **Browser install**: `/opt/homebrew/bin/python3.11 -m playwright install chromium`
- **Status**: ⚠️ Works but fails Turnstile on headless
- **Stealth API**: `Stealth().apply_stealth_async(page)` (NOT `Stealth(page)` or `stealth_js()`)
- **Turnstile**: GSMArena "Turnstile check" never resolves in headless mode
- **Pages saved**: /tmp/cf_page.png, /tmp/gsmarena_stealth4.png

### nodriver 0.50.3
- **Python**: 3.10+ (needs `str | Path` union syntax)
- **Install**: `/opt/homebrew/bin/python3.11 -m pip install nodriver`
- **Status**: ❌ Failed to connect to Chrome 149
- **Error**: `Failed to connect to browser` — Chrome 149's CDP debug port unreachable
- **Tried**: `no_sandbox=True`, explicit `browser_executable_path`, `browser_args`
- **Note**: May work with older Chrome or playwright-bundled Chromium

### zendriver 0.15.3
- **Python**: 3.10+
- **Install**: `/opt/homebrew/bin/python3.11 -m pip install zendriver`
- **Status**: ⚠️ Installed but not tested

### Turnstile-Solver ★821
- **Not tested**: patchright-based, supports multi-threaded execution and API integration

## Layer 3: C++-level

### Camoufox ★8998 / camofox-browser ★6395
- **Not tested**: Firefox fork with C++-level fingerprint
- **Has**: REST API, Docker, session isolation
