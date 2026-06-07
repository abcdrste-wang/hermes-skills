# 电商比价：淘宝 + 京东实战记录

> 用 Hermes + Playwright 搭淘宝/京东比价工具的经验总结

## 架构模式

```
Agent/LM ──调用──▶ python 脚本 ──Playwright──▶ Chromium（headless / GUI）
                      │
                      ├── Cookie 持久化（~/.hermes/pricer_cookies/）
                      ├── 商品页解析（CSS 选择器）
                      └── 结果格式化输出（对比表格）
```

不依赖 Agent 推理能力，纯浏览器自动化跑脚本更稳。

## 已知反爬与应对

### 淘宝
| 问题 | 对策 |
|------|------|
| 登录拦截 | 首次扫码登录 → 存 Cookie → 复用 |
| 搜索结果反爬 | Playwright 隐身模式 + 随机 UA |
| 页面结构频繁变更 | CSS 选择器用 fallback（多套 class 名轮询） |
| Cookie 有效期 | 一般 7-30 天，过期重跑 login |
| 无登录态搜索 | 可进入搜索页，但结果区域只显示"中国大陆/中国香港/中国台湾"地区选择，不渲染商品卡片。必须 Cookie 登录态才能触发商品渲染 |

### 京东
| 问题 | 对策 |
|------|------|
| 直接访问搜索页 → 跳验证页面（标题显示"京东验证"或"京东-欢迎登录"） | 必须从 jd.com 首页导航进入搜索，或用已登录 Cookie 从首页跳转。注意：即使有 Cookie，百度京东动态验证组件仍可能拦截 |
| Selenium/Playwright 检测 | `--disable-blink-features=AutomationControlled`，隐身模式 |
| 滑块验证码 | 无解 — 必须通过已登录态 Cookie 规避 |
| 商品列表 CSS 结构 | 新旧版京东共存，多 class 选择器轮询（`.gl-item` → `[class*='item']` → `[class*='goods-item']`） |
| 无登录态搜索 | 直接跳转登录页，无法获取任何商品数据（比淘宝更严 — 淘宝至少能进搜索页显示地区选择） |

### 拼多多
暂不支持的明确原因：
- 拼多多使用自定义 TCP 协议（非标准 HTTP），Playwright 无法模拟
- 移动端 H5 页面 + 强风控（设备指纹 + IP + 行为）
- 短生命周期 Token，即使登录成功频繁请求很快封号

## 脚本关键设计决策

1. **头拍模式**: login 必须 GUI（扫码），search 可以 headless
2. **Cookie 分开存储**: 淘宝和京东的 Cookie 互不影响，各自独立过期
3. **选择器多级 fallback**: 电商页面经常改结构，多套选择器兜底
4. **全量信息抓取**: 商品名 + 价格 + 店铺 + 销量 + 链接，最后算均价对比
5. **`--dryrun` 模式**: 跳过 Cookie 检查，供远程测试脚本连通性用。不产生有效商品数据，但可验证 Playwright 启动和 URL 访问正常。适用于 agent 在用户不在本机前时先验证脚本完整性

## 脚本位置

`~/.hermes/scripts/taobao_jd_pricer.py`

## 参考

- [Playwright anti-detection 参数](https://playwright.dev/docs/api/class-browsertype#browser-type-launch)
- 本机环境: Playwright 1.60 + Chromium 1223, Mac Mini M4/16GB, macOS 26.5.1
- 代理环境: V2rayU (HTTP 1087)
