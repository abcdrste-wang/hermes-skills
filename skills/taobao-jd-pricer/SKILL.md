---
name: taobao-jd-pricer
description: 淘宝 × 京东 商品比价工具。搜索指定关键词，在两个平台抓商品信息（价格、店铺、销量），输出对比表格。
trigger: 比价|价格对比|搜价格|淘宝.*京东|哪个平台便宜
---

# 淘宝 × 京东 比价

## 脚本位置

`~/.hermes/scripts/taobao_jd_pricer.py`

## 使用模式

```bash
# 首次登录（只需要一次，必须在你本机前操作）
python3 -u ~/.hermes/scripts/taobao_jd_pricer.py login

# 搜索比价
python3 ~/.hermes/scripts/taobao_jd_pricer.py search "机械键盘"
python3 ~/.hermes/scripts/taobao_jd_pricer.py search "小米13" --limit 10

# 远程测试连通性（不登录，只看脚本能否正常启动）
python3 ~/.hermes/scripts/taobao_jd_pricer.py search "test" --limit 1 --dryrun
```

## 工作流

### Phase 1: Login（一次性，必须本机操作）

1. 运行 `login` 命令
2. 弹出 Playwright 自带 Chromium 浏览器窗口（不是你日常用的 Chrome）
3. 依次扫码登录淘宝 → 京东
4. Cookie 保存到 `~/.hermes/pricer_cookies/{taobao,jd}.json`
5. 完成后浏览器关闭

**重要**：`login` 必须在本机操作——弹出浏览器窗口后，你需要拿起手机扫码。远程 SSH 无法完成。

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

### 京东
- 无登录态直接访问搜索页 → 跳验证页面（标题变"京东验证"）
- 有 Cookie 也可能会被前置验证拦截（百度京东动态验证组件）
- CSS 结构：`.gl-item` → `[class*='item']` → `[class*='goods-item']` 多级 fallback

### 拼多多（明确不支持）
- 使用自定义 TCP 协议（非标准 HTTP），Playwright 无法模拟
- 移动端 H5 页面 + 强风控
- Token 短生命周期，频繁请求很快封号

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

### 地区选择器遮挡

即使 Cookie 有效，京东搜索页会弹出「中国大陆/港澳/台湾」地区选择器模态框，
遮挡商品列表，导致什么都抓不到。

修复方法详见: `references/jd-region-selector-fix.md`

要点：
1. 搜索 URL 添加 `&area=1`（表示中国大陆）
2. 用 JS 设置 `ipLoc-djd` 和 `_gid` Cookie
3. 如果模态框仍弹出，自动定位并点击「中国大陆」
4. 等待 `wait_for_url()` 确保跳转到搜索结果页

### Cookie 生命周期

- 有效期一般 7-30 天
- 过期后必须重新 `login`（扫码）
- Cookie 文件是明文 JSON，存在 `~/.hermes/pricer_cookies/`

## 关联技能

详见 cloudflare-bypass-web-scraping 的 `references/ecommerce-price-comparison.md`（反爬策略 + CSS 选择器详解）和 `references/background-process-stdout-buffering.md`（背景进程输出问题）。
