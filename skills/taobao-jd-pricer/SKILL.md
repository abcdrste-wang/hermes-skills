---
name: taobao-jd-pricer
description: 淘宝 × 京东 商品比价工具。搜索指定关键词，在两个平台抓商品信息（价格、店铺、销量），输出对比表格。也覆盖 Hermes 做电商比价的能力评估和与 OpenClaw 的对比分析。
trigger: 比价|价格对比|搜价格|淘宝.*京东|哪个平台便宜|Hermes.*比价|OpenClaw.*比价|能比价吗|怎么比价
---

# 淘宝 × 京东 比价

## 脚本位置

`~/.hermes/scripts/taobao_jd_pricer.py`

## 使用模式

```bash
# 安装依赖（Hermes venv 中需要 Camoufox 用于京东反爬）
~/.hermes/hermes-agent/venv/bin/pip install camoufox

# 首次登录（只需要一次，必须在你本机前操作）
python3 -u ~/.hermes/scripts/taobao_jd_pricer.py login

# 搜索比价
python3 ~/.hermes/scripts/taobao_jd_pricer.py search "机械键盘"
python3 ~/.hermes/scripts/taobao_jd_pricer.py search "小米13" --limit 10

# 远程测试连通性（不登录，只看脚本能否正常启动）
python3 ~/.hermes/scripts/taobao_jd_pricer.py search "test" --limit 1 --dryrun
```

**注意：** 京东搜索使用 Camoufox（反指纹 Firefox），淘宝搜索使用 Playwright（Chromium）。两个浏览器引擎在同一个脚本中共存。京东搜索首次运行时会弹出 Firefox 窗口（headless=False），属于正常行为。

### Camoufox 坑（必读）

> ⚠️ **这三个坑是 Camoufox 在 GFW 环境下最常见的问题，每次集成必读。**

1. **类名是 `Camoufox`（同步版）或 `AsyncCamoufox`（异步版）**。`AsyncFirefox` 不存在，`from camoufox import AsyncFirefox` 报 `ImportError`。
2. **同步版构造器不支持 `viewport` 和 `geo` 参数**——`Camoufox` 内部把多余参数传给 `playwright.firefox.launch()`，两者都不是 Playwright launch 参数，报 `TypeError`。用 `page.set_viewport_size()` 设置视口，用 `locale='zh-CN'` 设语言。
3. **必须用 `DefaultAddons` 枚举传 `exclude_addons`** 跳过默认 uBlock 插件下载（GFW 下 `addons.mozilla.org` 返回 451）。正确写法：
   ```python
   from camoufox import Camoufox, DefaultAddons
   with Camoufox(headless=False, exclude_addons=[DefaultAddons.UBO]) as browser:
   ```
   ❌ `exclude_addons=['UBO']`（字符串，类型不匹配，排除无效）
   ❌ `addons=[]`（`add_default_addons()` 会把默认 addon 路径放回列表，`confirm_paths()` 仍然检查）
   ❌ `config={'geo': ...}`（`UnknownProperty: geo`，Camoufox config 里不存在这个 key）
4. **同步版和 Playwright 同步上下文可共存**——直接 `with Camoufox(...) as browser:` 在 `sync_playwright()` 块外。**不要用 `asyncio.run()`**——Playwright 同步上下文已有事件循环，会报 `RuntimeError`。
5. **首次运行自动下载 Firefox 引擎 298MB** 到 `~/Library/Caches/camoufox/`。下载中断需手动 `rm -rf ~/Library/Caches/camoufox/` 清理。详见 `references/camoufox-integration.md`。

## 输出格式总规范（核心工作流步骤）

在比价结果输出前，Agent **必须先**按「结论先行」的四段式结构组织输出，**再**做数据层面的后处理。

### 四段式输出结构（来自用户范文，对比/分析/推荐场景通用）

任何对比/分析/推荐场景（不仅限于比价），必须遵循这个结构：

```
结论先说：{一句话核心结论}

下面用和 {对比对象} 对比的方式讲清楚：

一、{主题}？能不能「{核心问题}」？
{直接回答 + 详细分析}

二、和 {对比对象} 的关键区别（你最关心的）
1. {方案A}：{特点}
   - {点1}
   - {点2}
2. {方案B}：{特点}
   - {点1}
   - {点2}

三、现实结论（一句话）
- {A} = 一句话定位
- {B} = 一句话定位

四、你该怎么选
- {场景1} → 推荐 {方案X}
- {场景2} → 推荐 {方案Y}
```

**比价场景的具体案例：** 见 `references/hermes-vs-openclaw-comparison.md`（用户亲笔范文，从「Hermes 能不能做比价」角度展示了完整结构）。

### 数据后处理规范

脚本原始输出可能包含以下噪音，Agent **必须**做后处理：

| 噪音类型 | 说明 | Agent 操作 |
|---------|------|-----------|
| 重复商品 | 淘宝推广链接可能让同一商品出现多次 | 按"店铺+标题"去重 |
| 空行条目 | CSS 选择器匹配到无内容的卡片占位 | 跳过任意字段为空的条目 |
| 推广链接 | `click.simba.taobao.com` 是跟踪链接 | 尝试提取直链，否则标注"推广链接" |
| 拆分价格 | 可能输出 `¥\n71\n.91` | 合并为 `¥71.91` |

**推荐输出格式：** 表格（按性价比排序）+ 单位价格计算 + 推荐结论。结论先行，先给表再给分析。详见 `references/agent-output-formatting.md`。

**⚠️ 强制流程（Agent 必须执行，不可跳过）：**

运行脚本获得原始输出后，Agent 必须执行后处理流程：
1. 删除完全重复的商品行
2. 删除标题/价格/店铺为空的无效行
3. 合并换行拆分的价格（`¥\n71\n.91` → `¥71.91`）
4. 从标题解析规格，计算单位价格
5. 按单位价升序排列
6. 给出 1-2 条推荐结论

❌ 不允许直接贴脚本原始输出给用户。
✅ 必须输出结构化对比表 + 推荐结论。

详见 `references/agent-output-formatting.md` 中的真实案例和所有噪音处理规则。

### Phase 1: Login（一次性，必须本机操作）

1. 运行 `login` 命令
2. 弹出 Playwright 自带 Chromium 浏览器窗口（不是你日常用的 Chrome）
3. 依次扫码登录淘宝 → 京东
4. Cookie 保存到 `~/.hermes/pricer_cookies/{taobao,jd}.json`
5. 完成后浏览器关闭

**重要**：`login` 必须在本机操作——弹出浏览器窗口后，你需要拿起手机扫码。远程 SSH 无法完成。

## 重要约束：用户不在 Mac 旁时

此任务的很多步骤（Camoufox FireFox 弹窗、京东扫码登录、调试浏览器问题）依赖用户操作本机。当用户说"已离开 Mac"或无法操作终端时：

1. **停掉所有非 headless 浏览器方案**（Camoufox headless=False、Playwright headed 模式）
2. **切换到纯 requests/API 方案**（如果目标平台有）
3. **或等用户回到电脑前再继续**

**不要** 在用户不在电脑前时继续调试需要弹浏览器的步骤——这会白白消耗用户时间。

### Phase 2: Search（可重复，可远程）

- 加载已保存的 Cookie
- headless 模式打开搜索页
- 抓取商品信息（多级 CSS 选择器兜底）
- 输出对比表格 + 两平台均价差

## 输出字段

| 字段 | 说明 |
|------|------|
| 商品名 | 标题（截断80字） |
| 价格 | ¥ 价格 |
| 店铺 | 店铺名 |
| 销量/评价 | 已售/评价数 |
| 链接 | 商品页 URL |

最后自动算两平台均价差。

## 反爬现实

### 淘宝
- 无登录态可打开搜索页，但结果区域显示的是"中国大陆/中国香港/中国台湾"地区选择（不显示商品）
- 必须 Cookie 登录态才能拿到商品数据
- CSS 结构：`[class*='Card']` / `[class*='item']` 多级 fallback
- 搜索页稳定可用：淘宝对 Playwright headless 容忍度较高

### 京东（严重风控）—— Camoufox 方案生效

#### 安装注意

参见上方「Camoufox 坑（必读）」第 3 条——必须传 `exclude_addons=[DefaultAddons.UBO]` 跳过已屏蔽的插件下载。插件缺失不影响核心功能。

首次运行 Camoufox 时会自动下载 Firefox 引擎（约 298MB），过程中会输出进度条和提取日志。（注意：本 skill 中不再重复安装细节，统一以顶部「Camoufox 坑」为准。）

#### 核心结论：京东搜索只能用 Camoufox（反指纹 Firefox），Playwright 完全不可行

京东 `search.jd.com` 的风控远超淘宝。2026-06-08 经验证：

**Playwright 全部失败的方法：**
- `page.evaluate()` JS 提取 DOM → 返回空（headless 检测到后渲染简化页，body 仅 6561 字符）
- 非 headless 模式 → 弹验证码（Playwright 的指纹已被京东标记）
- 纯 HTTP 请求（requests/curl）→ 全部 302 重定向或被 403 拦截
- `playwright-stealth` RPM 工具 → API 过时，不支持 Playwright 1.60+
- 注入 `navigator.webdriver = false` → 京东反向指纹检测不仅仅靠这一个指标
- 京东新版 React DOM 不再使用 `.gl-item`、`.p-name` 等旧类，新类名是 `_wrapper_1fqso_3` / `plugin_goodsCardWrapper`

**Camoufox（已验证可行）：**
- 安装在 Hermes venv：`~/.hermes/hermes-agent/venv/bin/pip install camoufox`
- 基于 browserforge 指纹库 + apify-fingerprint-datapoints，自动伪造真实浏览器指纹
- 使用 Firefox 内核（不是 Chromium），不在京东黑名单中
- 2026-06-08 验证：Camoufox `headless=False` 模式成功打开京东搜索页并抓取到数据
- **仍需要登录 Cookie**（扫码登录同 Playwright）
- **Cookie 结构：** 京东扫码登录的关键 Cookie 是 `pin`、`unick`、`pinId`、`_pst`、`thor`（不是 `pt_key`/`pt_pin`）。完整 Cookie 约 27 个 `.jd.com` 域条目，必须全部传入，只传核心 cookies 会让京东认为未登录
- **Cookie 注入方式：** Camoufox 必须逐条 `page.add_cookie()`，不支持 Playwright 的 `context.add_cookies()` 批量方式

#### 脚本中的实现

京东搜索使用 `search_jd_camoufox()` **同步函数**：
1. 加载 `~/.hermes/pricer_cookies/jd.json` Cookie
2. **`from camoufox import Camoufox`**（不是 AsyncCamoufox、不是 AsyncFirefox！必须是 `Camoufox`）
3. 启动 `Camoufox(headless=False, locale='zh-CN', exclude_addons=[DefaultAddons.UBO])` 反指纹浏览器
4. 先访问 jd.com 首页，注入 Cookie（逐条 `page.add_cookie()`）
5. 再刷新 jd.com → 跳转到 `search.jd.com/Search?keyword=xxx`
6. 用 `page.evaluate()` 遍历 `a[href*="item.jd.com/"]` 的父容器提取商品数据
7. 使用正则从文本块解析标题、价格、店铺、销量

#### API 选择

参见上方「Camoufox 坑（必读）」——同步版必须用 `Camoufox`（不是 `AsyncAsyncCamoufox`、不是 `AsyncFirefox`），不支持 `viewport` / `geo` 参数，需传 `exclude_addons=[DefaultAddons.UBO]`。安全参数：`headless=False`、`locale='zh-CN'`。

**商品提取策略（已更新 2026-06-08）：**
- 不再使用旧版 `.gl-item` / `.p-name` CSS 选择器（京东已改版，完全移除）
- 改用 `a[href*="item.jd.com/"]` 找到商品链接，向上遍历 6 层父容器
- 跳过 `.elevator` / `.shortcut` / `.mod_service` 等非商品容器
- 容器文本长度 40-800 chars 且含 ¥/￥ 符号才认为是有效商品容器
- 然后用正则从文本块解析标题/价格/店铺/销量

#### 风控恢复时间

- 一次触发的风控封锁约 24h 自动解除
- 账号级 + IP 级联合封禁：即使换浏览器，同一个账号在该 IP 下仍然被拦
- 24h 冷却期后首次搜索成功率高；但 **不要在同一 session 内连续搜索多次**
- 脚本中京东只搜一次，搜完关闭

### 拼多多（明确不支持）
- 使用自定义 TCP 协议（非标准 HTTP），Playwright 无法模拟
- 移动端 H5 页面 + 强风控
- Token 短生命周期，频繁请求很快封号

## "用户想买"场景处理流程

当用户说「直接上」「帮我买」「下单」等表达购买意愿时，Agent 按以下流程处理：

### Step 1: 判断能否自动购买
- 当前脚本 **仅限只读搜索**，不包含任何下单/支付功能
- Hermes 没有配置电商平台的下单权限（`tools.pay: deny`）

### Step 2: 告知限制，引导手动购买
回应用户的固定模式：
> "脚本只支持搜索比价，不支持自动下单。手动买的话，在淘宝搜 **'{精确关键词}'** 找到 **'{店铺名}'** 那家就行。"

具体信息应包括：
- 精确搜索关键词（含商品名+店铺名）
- 商品价格、规格
- 注意事项（如地区限购、运费等）

### Step 3: 如果需要进一步查看商品详情
有两种方式打开商品页：

**方式 A（推荐）— 让用户在浏览器自己搜：**
把搜索关键词告诉用户，让用户自己进去看。

**方式 B（尝试用 Hermes 浏览器帮看）— 注意 Cookie 隔离问题：**
```python
# ❌ 不行：Hermes browser 工具使用独立的浏览器会话，
#    不会自动携带 taobao_jd_pricer.py 保存的 Cookie
browser_navigate("https://item.taobao.com/xxx")
→ 结果是未登录页面/验证码拦截

# ✅ 正确：通过脚本的 Playwright 会话打开
# 但需要用户本机能弹出浏览器窗口（本地非 headless）
```

**Cookie 隔离陷阱（重要）：**
Hermes 的 `browser_navigate` / `browser_vision` 工具使用完全独立的浏览器会话，不会自动加载 `~/.hermes/pricer_cookies/taobao.json` 中的 Cookie。尝试用 Hermes 内置浏览器打开淘宝商品页会导致：
- 未登录状态（显示首页而非商品页）
- 验证码拦截（滑块验证）
- "亲，请登录"弹窗

这意味着：**当用户要求看商品详情时，告诉用户搜索关键词让用户自己打开，比尝试用 Hermes 浏览器更可靠。**

## Hermes 集成注意点

### Background process stdout 缓冲问题

用 `terminal(background=True)` 启动 login 脚本时，必须用 `python3 -u`：

```bash
# ❌ 不行：输出被缓冲，process(log=...) 看不到任何内容
python3 ~/.hermes/scripts/taobao_jd_pricer.py login

# ✅ 正确：-u 禁用缓冲，实时输出
python3 -u ~/.hermes/scripts/taobao_jd_pricer.py login
```

无 TTY 状态下 Python 默认全缓冲（4KB/8KB block），`-u` 切换到无缓冲。

确认脚本确实在运行的方法：`ps aux | grep chromium` 看浏览器进程是否已启动。

## 京东特有坑

### 京东搜索风控（最难解决的问题）

**现状：** 京东 `search.jd.com` 的风控极严。即使有登录 Cookie + Camoufox，首次被风控后仍需等待 24h 冷却期。

**关键教训（2026-06-07 / 2026-06-08 三次证实）：**
1. 新登录 Cookie 首次搜索能成功看到页面 → 地区选择器遮挡
2. 补完地区选择逻辑后**同 Session 内重试** → 账号被风控标记，后续搜索全部被拦
3. Camoufox 能绕过指纹检测（正常加载页面），但无法绕过账号级风控封锁
4. 风控是账号级+IP级联合封禁，且同次浏览器 session 内连续操作会触发阈值

### 地区选择器（2026 年 618 前新形态）

2026年6月京东搜索页的地区选择器可能已从**模态框 overlay** 改为**独立重定向页面**（`/area?keyword=xxx`）。修复脚本需要同时处理两种形态。详见 `references/jd-region-selector-fix.md`。

核心原则：
1. **脚本只搜一次，搜完关闭**
2. **被风控后不要重试**，等 24 小时
3. 首次测试先用 `--dryrun` 验证 Cookie 是否加载成功
4. 不能在开发过程中反复搜索同一关键词

### 如何运行 login

```bash
# 注意：必须用 Hermes venv 的 Python，系统 python3 可能缺乏依赖
# 推荐用绝对路径运行：
# ~/.hermes/hermes-agent/venv/bin/python3

# 首次登录（本机操作，会弹出浏览器窗口）
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/scripts/taobao_jd_pricer.py login

# 搜索（可远程）
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/scripts/taobao_jd_pricer.py search "商品名"

# 远程测试连通性
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/scripts/taobao_jd_pricer.py search "test" --limit 1 --dryrun
```

⚠️ **venv 路径问题**：用户系统 `python3` 可能指向不同的 Python 版本（如 3.9），而 Playwright 装在 Hermes venv（3.11）中。通过 `~/.hermes/hermes-agent/venv/bin/python3` 运行可确保依赖完整。安装 Playwright 也需用 venv 的 pip：`~/.hermes/hermes-agent/venv/bin/pip install playwright`### Cookie 生命周期

- 有效期一般 7-30 天
- 过期后必须重新 `login`（扫码）
- Cookie 文件是明文 JSON，存在 `~/.hermes/pricer_cookies/`

## ❗ 安全铁律（只读，禁止下单）

**此脚本仅限搜索和读取商品信息**，不包含任何下单/加购物车/支付的代码逻辑：

- 脚本只调用搜索 API 和商品列表页面
- 无点击「立即购买」「加入购物车」「提交订单」等功能
- 无用户地址、支付信息、订单数据的读取或写入
- 绝对不允许 Hermes Agent 通过此脚本自动下单

> 📕 **AI Agent 支付安全完整架构**详见 `references/agent-payment-safety.md`，涵盖了：
> - 三类核心权限（Agent 权限 / 平台授权 / 支付授权）
> - 5 步操作流程
> - 6 条安全铁律（最小权限、账户隔离、每笔确认、限额时效、全程日志、禁用无障碍模式）
> - 各平台（淘宝/京东/12306/美团）对接方式和安全边界
> - 此脚本的铁律定位

## 关联技能

详见 cloudflare-bypass-web-scraping 的 `references/ecommerce-price-comparison.md`（反爬策略 + CSS 选择器详解）和 `references/background-process-stdout-buffering.md`（背景进程输出问题）。

---

## 分享给其他人

另一个 Hermes 要安装这个比价技能，给 Ta 仓库地址和安装步骤：

1. **专用仓库地址：** `https://github.com/abcdrste-wang/hermes-china-skills`（只包含中国区域技能，干净独立）
2. 在中国需代理克隆：`ALL_PROXY=socks5://127.0.0.1:1080 git clone --depth 1 https://github.com/abcdrste-wang/hermes-china-skills.git`
3. 复制 `skills/taobao-jd-pricer` 到 `~/.hermes/skills/`
4. 复制 `scripts/*.py` 到 `~/.hermes/scripts/`
5. 首次运行 `python3 taobao_jd_pricer.py login` 扫码

详细的逐步指南（含验证步骤和常见问题）见 `references/skill-sharing-guide.md`。

> ⚠️ 注意：SkillDock.io 的发布功能尚未开放（2026-06-07 确认 Publish 页面为占位符），暂时只能通过 GitHub 仓库分发。

## 参考文档

此技能目录下的参考文档：
|------|------|
| `references/agent-payment-safety.md` | AI Agent 支付安全架构和铁律 |\n| `references/jd-region-selector-fix.md` | 京东地区选择器遮挡问题的修复方法 |\n| `references/jd-anticrawl-debug-log.md` | 京东风控排查日志（含 MCP 可行性分析） |\n| `references/camoufox-integration.md` | Camoufox 反指纹浏览器安装、API、与 Playwright 混合使用 |\n| `references/agent-output-formatting.md` | 比价结果输出格式化规范和模板 |
| `references/skill-sharing-guide.md` | 将此技能分享给另一个 Hermes 的安装指南 |
| `references/hermes-vs-openclaw-comparison.md` | Hermes vs OpenClaw 电商比价能力对比分析（用户亲笔范文） |
