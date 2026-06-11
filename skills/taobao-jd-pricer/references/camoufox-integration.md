# Camoufox 集成记录 (2026-06-08, 更新 2026-06-09)

## 背景

京东搜索 `search.jd.com` 对 Playwright（Chromium）有强风控检测。Playwright 的各种反检测手段（非 headless、注入 JS、stealth 插件）均无法可靠绕过。Camoufox 提供了一个基于 Firefox + 真实浏览器指纹的替代方案。

## 安装

```bash
~/.hermes/hermes-agent/venv/bin/pip install camoufox
```

Camoufox 自动依赖 browserforge（指纹生成库）和 apify-fingerprint-datapoints（真实浏览器指纹数据集）。

首次运行时自动下载 Firefox 引擎（约 298MB）和 uBlock Origin 插件（GFW 下 `addons.mozilla.org` 下载可能 451 失败，不影响功能）。

## ⚠️ API 类型（实测修正版 2026-06-08）

Camoufox 提供**两种 API + 两个类名**，看清不要搞混：

| API | 类名 | 导入路径 | 适用场景 |
|-----|------|---------|---------|
| 同步 (sync) | **`Camoufox`** | `from camoufox import Camoufox` | 与 Playwright `sync_playwright()` 在同一个脚本混用 |
| 异步 (async) | **`AsyncCamoufox`** | `from camoufox import AsyncCamoufox` | 纯异步脚本 |

**❌ `AsyncFirefox` 不存在！`from camoufox import AsyncFirefox` 会报 `ImportError: cannot import name 'AsyncFirefox'`**

## 首次运行：自动下载 Firefox 引擎（~298MB）

Camoufox 首次使用时自动下载并提取 Firefox 引擎到 `~/Library/Caches/camoufox/`。下载过程输出进度条和 `Extracting Camoufox: ...` 日志，属于正常行为。后续不会再下载。

注意：中断的半成品 addon 下载可能导致后续每次启动都失败。修复方法：
```bash
rm -rf ~/Library/Caches/camoufox/addons/
```

## ⚠️ 必须避开 `addons.mozilla.org`（中国 GFW）— 枚举陷阱

Camoufox 默认尝试下载 uBlock Origin 插件（从 `addons.mozilla.org`）。在中国 GFW 下访问该域返回 451，导致插件下载失败。

**Camoufox 的错误行为模式（源码级别）：**
1. `camoufox/addons.py` 的 `add_default_addons()` 向 addons 列表添加默认插件路径
2. 即使传 `addons=[]`，代码仍然调用 `add_default_addons()` 往列表里加
3. 如果下载失败（例如之前下载到一半被中断），插件目录存在但缺少 `manifest.json`
4. `confirm_paths()` 检查到不完整插件 → 抛出 `InvalidAddonPath`

**必须使用 `exclude_addons` 参数排除默认插件，而且要用枚举值：**

```python
# ❌ 全部失败：
with Camoufox(addons=[]) as browser:       # InvalidAddonPath — 仍调 add_default_addons()
with Camoufox() as browser:                # InvalidAddonPath — 默认下载 uBlock，GFW 下失败
with Camoufox(exclude_addons=['UBO']) as browser:  # ❌ 字符串也不行！类型不匹配，exclude 不生效
with Camoufox(geo=...) as browser:         # TypeError: unexpected keyword argument 'geo'

# ✅ 正确：传 DefaultAddons 枚举值
from camoufox import DefaultAddons
with Camoufox(exclude_addons=[DefaultAddons.UBO]) as browser:
```

`exclude_addons` 接受 `DefaultAddons` **枚举值列表**（不是字符串！）。`'UBO'` 字符串类型不匹配，`exclude addons` 的内部比较是 `if addon not in exclude_list`，枚举值 `DefaultAddons.UBO` 与字符串 `'UBO'` 的比较永远为 False，所以 exclude 不生效。

## 关键限制：同步 API 不支持 viewport / geo 参数

```python
# ❌ TypeError: launch() got an unexpected keyword argument 'viewport'
with Camoufox(viewport={"width": 1280, "height": 900}) as browser:

# ❌ TypeError: launch() got an unexpected keyword argument 'geo'
with Camoufox(geo={"region": "zh-CN", "timezone": "Asia/Shanghai"}) as browser:

# ❌ UnknownProperty: Unknown property geo in config
with Camoufox(config={"geo": {"region": "zh-CN", "timezone": "Asia/Shanghai"}}) as browser:

# ✅ 正确用法
with Camoufox(headless=False) as browser:
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 900})
```

Camoufox 同步 API 内部调用 `launch_options()` 处理参数，但 `viewport`/`geo`/`window` 等参数通过 `**launch_options` 透传给 Playwright 的 `browser_type.launch()`，Playwright 不接受这些参数。

- ✅ `headless` — 支持
- ✅ `exclude_addons` — 支持（枚举值）
- ✅ `locale` — 支持
- ❌ `viewport` — 不支持，用 `page.set_viewport_size()`
- ❌ `geo` — 不支持，用 `geoip=True`
- ❌ `config={'geo': ...}` — 不支持，Camoufox 的 validate_config 不识别

## 基础用法（同步版，与 Playwright 混用）

```python
from camoufox import Camoufox, DefaultAddons

def search_jd_sync():
    jd_cookies = json.loads(open("jd.json").read())
    
    with Camoufox(
        headless=False,  # 京东风控严格，必须非 headless
        exclude_addons=[DefaultAddons.UBO],  # GFW 下 uBlock 下载会 451
        locale='zh-CN',
    ) as browser:
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})
        
        # 先访问首页
        page.goto("https://www.jd.com", timeout=30000)
        page.wait_for_timeout(2000)
        
        # 逐条注入 Cookie（注意：Camoufox 不支持批量 add_cookies，必须逐条）
        for c in jd_cookies[:30]:
            try:
                page.add_cookie({
                    "name": c["name"],
                    "value": c["value"],
                    "domain": c.get("domain", ".jd.com"),
                    "path": c.get("path", "/"),
                })
            except Exception:
                pass
        
        # 刷新让 Cookie 生效
        page.goto("https://www.jd.com", timeout=20000)
        page.wait_for_timeout(2000)
        
        # 搜索
        search_url = f"https://search.jd.com/Search?keyword={keyword}&enc=utf-8"
        page.goto(search_url, timeout=30000)
        page.wait_for_timeout(5000)
        
        # 提取 DOM
        raw = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('a[href*="item.jd.com/"]').forEach(a => {
                // ... 同 Playwright evaluate API
            });
            return results;
        }""")
```

## 和 Playwright 同步 API 在同一脚本中混用

**核心约束：** Playwright 的 `sync_playwright()` 运行在同步上下文中，会在内部维护一个事件循环。此时不能调用 `asyncio.run()` 来运行 Camoufox 异步版，否则会报：

```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**解决方案：** 使用 Camoufox **同步版 `Camoufox`**（不是 AsyncCamoufox）：

```python
from playwright.sync_api import sync_playwright
from camoufox import Camoufox  # 同步版

def cmd_search(keyword, limit=5):
    with sync_playwright() as p:
        # 淘宝用 Playwright
        browser = p.chromium.launch(headless=True)
        # ... 淘宝搜索 ...
        
        # 京东用 Camoufox（同步，不用 asyncio.run）
        items = []
        from camoufox import Camoufox, DefaultAddons
        with Camoufox(headless=False, exclude_addons=[DefaultAddons.UBO]) as cf_browser:
            page = cf_browser.new_page()
            # ... 京东搜索 ...
            items = extract_items(page)
        
        print(items)
```

## 已知限制

1. **只能非 headless**：`headless=True` 模式下京东可能仍能检测到，推荐始终用 `headless=False`
2. **会弹 Firefox 窗口**：每次执行搜索会短暂弹出 Firefox 窗口，约 10-15 秒后自动关闭
3. **Cookie 依赖**：Camoufox 不解决 Cookie 问题，仍需首次 Playwright 扫码登录生成 Cookie
4. **第一方库异常处理**：Camoufox 的 `except_logger` bug 可能导致警告日志，不影响功能
5. **仍受风控影响**：Camoufox 绕过的是指纹检测，不是风控封锁。如果 Cookie 已被风控标记（24h 冷却期），Camoufox 也无法解封
6. **uBlock Origin 下载失败**：GFW 阻止 `addons.mozilla.org` 导致 uBlock 下载失败（451），但不影响功能
