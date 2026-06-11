# 京东地区选择器修复记录

## 问题现象

登录京东后（Cookie 有效），执行 `search` 命令时 Playwright 打开搜索页，
页面上弹出一个「中国大陆/港澳/台湾」地区选择器模态框，
覆盖整个商品列表区域，导致 CSS 选择器 `[class*='item']` 抓不到任何结果。

## 根因

京东会在以下场景弹出地区选择器：
- 首次从新 IP/设备访问（即使有 Cookie）
- Cookie 中 `_gid` / `areaId` 等地理标记缺失或过期
- 浏览器指纹发生变化（headless vs headful 切换）

## 修复方案

在 `search_on_jd()` 函数中，商品列表加载之前增加一段 JavaScript 执行：

```python
# 先尝试用 JS 直接设置地区 Cookie + 跳转（最可靠）
page.evaluate("""
    document.cookie = "ipLoc-djd=1-72-2799-0; domain=.jd.com; path=/";
    document.cookie = "_gid=CN-1; domain=.jd.com; path=/";
""")
```

然后在 URL 中添加 `&area=1` 参数触发跳转到指地区：

```
https://search.jd.com/Search?keyword=机械键盘&enc=utf-8&area=1
```

如果仍需点击（兜底方案）：

```python
# 查找地区选择器弹窗并选择「中国大陆」
try:
    region_modal = page.locator("div.region-selector, div.J_regionSelector, [class*='region']")
    if await region_modal.is_visible(timeout=3000):
        mainland = page.locator("a:has-text('中国大陆'), span:has-text('中国大陆'), div:has-text('中国大陆')").first
        await mainland.click()
        await page.wait_for_timeout(2000)
except:
    pass
```

## 关键参数

- `area=1` 在 URL 中 = 中国大陆（京东区域编码：1 = 北京/全国）
- `ipLoc-djd=1-72-2799-0` = 中国大陆·全国
- `_gid=CN-1` = 中国大陆

## 2026-06-08 新发现：地区选择器形态可能已变化

### 现象
新 Cookie 首次搜索时，地区选择器不再以模态框形式弹出，而是**重定向到独立地区选择页**（URL 变为 `/area?keyword=xxx`）。搜索页本身没有弹窗，而是整个页面被替换为地区选择页。

### 处理逻辑
```python
# 选择中国大陆后，等待自动跳回搜索结果页
page.goto(f"https://search.jd.com/Search?keyword={kw}&enc=utf-8&area=1", ..., timeout=30000)
page.wait_for_timeout(5000)

# 检查是否被重定向到地区选择页
if "area" in page.url and "Search" not in page.url:
    page.wait_for_timeout(10000)  # 等待自动跳转
    if "Search" not in page.url:
        # 重试一次
        page.goto(search_url, ..., timeout=30000)
        page.wait_for_timeout(5000)
```

### 🚨 关键陷阱：同会话重试触发风控
**同一 Playwright session 内**修复代码后立即重试搜索，京东会触发账号风控。风控后返回"抱歉由于访问频繁导致无法搜索"，且 24h+ 才能解封。

**核心原则：**
1. 脚本只搜一次，搜完关闭
2. 被风控后不要重试，等 24 小时
3. 首次测试先用 --dryrun 验证 Cookie 是否加载成功
4. 不能在开发过程中反复测试
