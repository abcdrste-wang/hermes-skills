# 探查闭源 Electron 应用是否暴露 API/MCP 接口

## 背景

在尝试将淘宝桌面版（Electron Mac 客户端）作为 MCP 桥接源时，需要系统性地探查它是否暴露了任何可编程接口。

## 探查步骤（按顺序）

### 1. 进程确认

```bash
ps aux | grep -iE 'taobao|tb' | grep -v grep
# 返回应用名和 PID（如 73452）
```

### 2. 端口扫描

```bash
# 查找所有 LISTEN 端口
lsof -i -P -n | grep -i taobao | grep LISTEN

# 或者按 PID 查
lsof -p 73452 -i -P -n
```

**常见发现：**
- 淘宝桌面版没有对外暴露 HTTP 端口
- 端口 40000 是 Electron `SingletonSocket`（写在 `Local State` 文件里），仅用于进程间锁，不是 HTTP 服务
- Electron 应用默认不开远程调试端口

### 3. HTTP 服务探测

```bash
# 对发现的端口尝试常见路径
curl -s -m 5 http://127.0.0.1:40000/        # 超时 = 不是 HTTP
curl -s -m 5 http://127.0.0.1:40000/api
curl -s -m 5 http://127.0.0.1:40000/mcp

# nc 快速探测
(echo -e "GET / HTTP/1.0\r\nHost: 127.0.0.1:40000\r\n\r\n" | nc -w 5 127.0.0.1 40000) | head -c 500
```

### 4. Chrome DevTools Protocol (CDP) 检查

```bash
for port in 9222 9223 9229 9230; do
  curl -s -m 2 http://127.0.0.1:$port/json/version
done
```

**注意：** Electron 应用启动时默认不开启 `--remote-debugging-port`，所以一般找不到 CDP 端口。

### 5. 应用包分析（须解压 app.asar）

```bash
# 安装 asar 工具
npx -y asar list /path/to/Electron.app/Contents/Resources/app.asar | head -50

# 提取
mkdir -p /tmp/app_asar
npx -y asar extract /path/to/Electron.app/Contents/Resources/app.asar /tmp/app_asar

# 搜索关键字符串
grep -i 'mcp' /tmp/app_asar/out/main/index.js | head -20
grep -i 'localhost\|server\|http.create\|express\|port.*listen' index.js | head -10
grep -i 'debug\|9222\|9229\|inspector\|devtools' index.js | head -10
```

**注意事项：**
- 商业应用（尤其是阿里系）的 JS 代码通常高度混淆（变量名 `_0x...`, `_0x_0x...`），直接搜字符串能找到但难以阅读
- 搜索关键词比预期要宽泛：`mcp`（MCP 协议）、`server`（内置 HTTP 服务）、`plugin`（插件系统）、`bridge`、`rpc`、`protocol`
- 淘宝桌面版主进程约 4.3MB，混淆后单文件无源映射

### 6. 应用数据目录检查

```bash
ls -la ~/Library/Application\ Support/<appname>/
```

查找 `plugins/` 目录、`extensions/`、`.config` 文件。

### 7. 结果解读

| 发现 | 含义 |
|------|------|
| ❌ 无 HTTP 端口 LISTEN | 无 RPC/API 服务 |
| ❌ 无 CDP 端口 | 不能通过 DevTools 协议远程控制 |
| ❌ 无插件目录 | 不支持第三方扩展 |
| ✅ 有 app.asar | 可以通过提取分析内部逻辑 |

**淘宝桌面版结论（2026-06）：** 纯 Electron 包裹的内嵌 Web 外壳，无任何外部可编程接口。本质上 = 浏览器 + 地址栏锁定在淘宝首页。不适合做 MCP 桥接源。

### 8. 替代方案（当应用无 API 时）

1. **浏览器自动化（Playwright）** — 模拟用户操作，不需要应用提供 API
   - 优点：通用性强，任何 Web 应用都能操作
   - 缺点：反爬/风控问题，速度慢
2. **应用内部注入** — 通过 `app.getPath('exe')` 加 `--remote-debugging-port` 等实验性参数重启
   - 非标准化，不推荐
3. **操作系统级自动化** — macOS Accessibility API、CGEvent 模拟
   - 淘宝桌面版是 Electron，UI 不在原生控件层，Accessibility API 只看到 `WebView` 一个控件
