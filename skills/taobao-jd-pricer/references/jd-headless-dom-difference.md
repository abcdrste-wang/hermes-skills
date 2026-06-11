# 京东 headless DOM 差异分析 (过时) 

> ⚠️ **此文档已过时。** 2026-06-08 开始京东搜索改用 Camoufox（反指纹 Firefox），不再使用 Playwright headless 模式。
> 保留此文件仅作为历史参考。

## 原问题描述（2026-06-07）

在 Playwright headless 模式下，京东 `search.jd.com` 返回的 DOM 结构与正常浏览器完全不同：

- Body 长度仅 6561 字符（vs 正常页面数万字符）
- 无 `.gl-item`、`p-price`、`p-name` 等标准选择器
- 商品数据通过 React hydration / Ajax 延迟加载，headless 模式下被阻断
- 但视觉截图看起来正常（商品卡片、价格、品牌都有显示）

## 验证过程

1. headless 截图 `/tmp/jd_headless.png` 显示商品列表视觉正常
2. 但 DOM 中查询所有容器/价格/名称元素全部返回空
3. 打印所有 `<a[href*="item.jd.com/">` 数量为 0
4. 非 headless 模式下直接弹验证码

## 被替代的原因

Playwright headless → 京东可检测到 `navigator.webdriver=true`、缺失特定 API 等指纹特征，直接返回简化版 DOM。
Playwright 非 headless → 京东指纹库匹配到 Playwright 特征，弹验证码拦截。
→ 两个方向都走不通，最终改用 Camoufox（Firefox 内核的指纹伪造浏览器）。
