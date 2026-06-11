# 京东搜索风控排查日志（2026-06-07）

## 背景

Playwright 脚本 `taobao_jd_pricer.py` 搜索京东时返回「抱歉由于访问频繁导致无法搜索，请稍后再试」。

## 排查路径（按顺序）

### 1. Cookie 是否有效？
```
page.goto('https://www.jd.com/')
page.query_selector('.nickname')  →  'jd_AkdwUGzAR...'
```
✅ 登录有效，昵称正常显示。Cookie 不是原因。

### 2. headless 模式问题？
```
browser = p.chromium.launch(headless=False)   # 非 headless
```
❌ 仍然风控。非 headless 无用。

### 3. 反检测库？
```
pip3 install playwright-stealth
from playwright_stealth import Stealth
Stealth().hook_playwright_context(ctx)
```
❌ API 不兼容（v2.0.3 的 hook_playwright_context 期望 BrowserType 而非 BrowserContext，与 Playwright 1.60 不匹配）。

### 4. 注入 JS 移除 webdriver 标记？
```
page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false });")
```
❌ 仍然风控。JD 风控检测程度更深。

### 5. 全新 persistent profile？
```
browser = p.chromium.launch_persistent_context(user_data_dir='/tmp/jd_fresh_profile')
```
❌ 仍然风控。与浏览器状态无关。

### 6. 纯 HTTP 请求？
```
curl -s 'https://search.jd.com/Search?keyword=机械键盘' → 302 Found
requests.get('...') → timeout (30s hang)
```
❌ HTTP 层面也被拦截，不依赖浏览器指纹。

### 7. 账号/IP 级别封禁确认
自己打开正常的 Chrome 浏览器 → 访问 `search.jd.com` 输入「机械键盘」→ 如果也显示「访问频繁」，说明是**账号级封禁**。

## 根因

京东风控系统（JAS）检测到：
1. 同一账号短期内从同一 IP 发起大量搜索请求（前面调试过程中重试了十几次）
2. 618 大促期间风控阈值大幅降低
3. 一旦触发，IP+账号组合被临时加入黑名单

## 京东风控 vs MCP 插件

### 问题结论：安装 MCP 插件不能解决京东搜索风控。

**详细解释：** MCP（Model Context Protocol）是给 Agent 提供标准化工具接口的协议（暴露例如 `search_product`、`create_order` 这类函数）。底层走的还是 HTTP API 或浏览器自动化。

京东的问题不在接口形式，而在于：
- 京东**没有开放的商品搜索 API**（不像淘宝有淘系 API）
- 京东所有公开搜索接口（`search.jd.com`、`so.jd.com`、移动端 H5）都被风控系统保护
- 就算用 MCP 包装了京东接口，底层调的还是那些被风控的 URL
- 因此 MCP 和风控是两个不同维度的问题

### 各平台 MCP 可行性对比

| 平台 | 开放 API | 风控强度 | Playwright 可靠性 | MCP 能解决风控？ |
|------|---------|---------|-----------------|----------------|
| 淘宝 | ✅ 有（淘系/千牛） | 中 | ✅ 稳定 | 不相关（API 本身可用） |
| 京东 | ❌ 无 | 极高（618 尤甚） | ❌ 频繁被拦 | ❌ 不能（底层还是被封）|
| 12306 | ❌ 无开放 API | 中 | ✅ 可用（但不如直接调公开 API） | 不相关 |

### taobao-mcp-demo 插件真相

当前 npm 上唯一的淘宝 MCP 包是 `taobao-mcp-demo`（v1.0.8），于 2025-07-29 发布。这个包**实际上是个空壳**：虽然包内有 `tools/taobao-search.js` 文件，但 `tools/index.js` 中**已将其注册代码注释掉了**，实际注册的四个工具是 `add`/`sub`/`mul`/`div`（加减乘除），与淘宝无关。

真正可用的淘宝 MCP 服务器需要：
1. 在淘宝开放平台（https://open.taobao.com）注册开发者、创建应用获得 App Key + Secret
2. 或者自建 MCP 服务，把现有的 `taobao_jd_pricer.py` 包装为 stdio MCP 服务器

**2026年6月结论：没有现成的、可用的淘宝 MCP 插件。**

## 2026-06-08 补充：非 headless 首次搜索可通，但同 Session 重试触发风控

### 现象

本次会话中发现了与「访问频繁」不同的另一个模式：

**第一次**非 headless 搜索：✅ 成功加载搜索页，商品可见，但被**地区选择器遮挡**（不是风控）
**修复地区选择器后立即重试**（同一次 Playwright session，间隔 < 5 分钟）：❌ 返回「抱歉由于访问频繁导致无法搜索」

### 关键教训

1. **地区选择器遮挡 ≠ 风控拦截** — 两者表现不同，需要不同处理
2. **同次 session 内连续操作会触发阈值** — 即使是合法的 Cookie + 非 headless
3. **「新登录 Cookie + 首次搜索」是黄金窗口** — 只有这一次机会能拿到数据，之后账号即被标记

### 实操建议

开发调试京东搜索时：
- 不要在开发过程中反复搜索同一关键词
- 先把整个流程逻辑完全写对，**最后一次测试**
- 如果必须多次测试，使用不同关键词或间隔 24 小时
- 地区选择器处理逻辑必须在首次搜索前就写好，因为首次搜索修复后重试触发风控就来不及了

### 对脚本的影响

脚本当前策略：`headless=False` 模式运行京东搜索，一次搜索完成立即关闭浏览器。不保留浏览器复用。

- **换 IP**：换网络环境（手机热点、VPN 出口）可绕过 IP 限制。
- **换账号**：换一个京东账号可以立即搜索。

## 最佳实践（避免触发）

1. 搜索间隔至少 3 秒（加 `page.wait_for_timeout()`）
2. 每次搜索之间**不要重复刷新/重试**——被风控后的重试只会延长封禁
3. 同一个脚本同一 session 只搜一次，搜完就关浏览器
4. 如果返回风控，停止操作 24 小时
5. 首次上线时先用 `--dryrun` 在小范围验证，不要直接跑大量搜索
