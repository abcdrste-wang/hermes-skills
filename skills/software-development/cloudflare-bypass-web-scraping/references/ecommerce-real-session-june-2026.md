# Taobao + JD Real Login Session (June 2026)

## Environment

- macOS 26.5.1, Mac Mini M4 (16GB)
- Playwright 1.60.0, Chromium-1223
- Python 3.11 (Homebrew)
- Proxy: V2rayU (HTTP 127.0.0.1:1087), NOT used for domestic e-commerce
- Headless mode for search, non-headless (GUI) for login

## Taobao — Login + Search

### Login flow (GUI, one-time)
1. `python3 taobao_jd_pricer.py login` — opens Chromium window
2. Script navigates to taobao.com, waits for user to scan QR code
3. After successful QR scan, browser redirects to homepage
4. Script detects `wait_for_url("https://www.taobao.com/")` as login success
5. Then navigates to `https://www.jd.com/` for JD login (same session)
6. Cookies saved to `pricer_cookies/taobao.json` and `jd.json`

### Search (headless, with cookies)
```
python3 taobao_jd_pricer.py search "机械键盘" --limit 3
```

**Result: ✅ SUCCESS** — returned real product data:
- 狼蛛F2088 机械键盘 ¥115 已拼1万+件
- AKKO 3087DS ¥197 已售2万+
- 前行者V87 ¥69.9 1万+人付款
(all with clickable links)

### URL structure
Taobao search URL: `https://s.taobao.com/search?q={keyword}`
Links from search results use taobao affiliate short URLs:
`click.simba.taobao.com/cc_im?` — these redirect to real product pages.

## JD — Region Selector Blocking Search

### Problem
Even with valid cookies, `search_on_jd()` opens `https://search.jd.com/Search?keyword={keyword}` and gets:
1. A modal "中国大陆/港澳/台湾" region selector overlay
2. No product elements in DOM (CSS selectors find nothing)

### Root cause
The `area` parameter in JD search URL defaults to nothing when loaded via
Playwright's `page.goto()`. A browser user clicking through JD homepage has
`area=1` (or another region code) set automatically via cookies + session.

### Fix applied
Set `area=1` in URL to indicate mainland China:
```python
url = f"https://search.jd.com/Search?keyword={keyword}&enc=utf-8&area=1"
```

Additionally, JS cookie injection:
```python
page.evaluate("""
    document.cookie = "ipLoc-djd=1-72-2799-0; domain=.jd.com; path=/";
""")
```

### Current status
After fix: **search successfully navigates** to JD search results page
(confirmed via `wait_for_url`). However, the exact product extraction
was not verified due to the region selector modal appearing intermittently.

### CSS selectors for JD
Primary: `.gl-item` (standard JD listing)
Fallback: `[class*='item']`, `[class*='goods-item']`

## Key Lessons

1. **JD search URL needs `area=1`** — without it, region selector blocks everything
2. **Taobao works fine with just cookies** — no URL parameter tricks needed
3. **Cookie file format**: Playwright `context.cookies()` produces a JSON array of dicts with keys: `name`, `value`, `domain`, `path`, `expires`, `httpOnly`, `secure`, `sameSite`
4. **Login must be run on the actual machine** with a display (QR scan requires user interaction)
5. **Search can be run headless remotely** — just needs valid cookie files
