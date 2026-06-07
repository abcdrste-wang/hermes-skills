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
    document.cookie = "_gid=1-72-2799-0; domain=.jd.com; path=/";
""")
await page.goto(f"https://search.jd.com/Search?keyword={keyword}&enc=utf-8&area=1")
await page.wait_for_timeout(2000)
```

如果仍弹出地区选择器模态框，自动点击「中国大陆」选项：

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
- 完整区域编码格式：`province-city-county-town`（如 `1-72-2799-0`）
- `ipLoc-djd` 和 `_gid` Cookie 控制京东地域感知

## 验证方法

```python
# 在 search_on_jd 中增加日志
print("[JD] URL after region fix:", page.url)
# 查看页面是否有商品 element
item_count = await page.locator("[class*='item']").count()
print(f"[JD] Item elements found: {item_count}")
```

## 完整实现参考

在 `taobao_jd_pricer.py` 中 `search_on_jd()` 函数的实现（约 2026-06-07 版本）：

1. 第 130 行附近：加载 Cookie 后设置 `area=1` 的 URL 参数
2. 第 150-170 行：地区选择器检测 + 自动点击
3. 第 180 行：10 秒的 `page.wait_for_url()` 确保跳转到搜索结果页
