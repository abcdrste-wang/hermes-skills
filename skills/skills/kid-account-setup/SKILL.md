---
name: kid-account-setup
description: 用 Hermes 给孩子搭建独立 AI 助手的完整方案。独立实例、飞书机器人、权限控制、模板文件。配套 GitHub 仓库提供完整教程和模板。
---

# Kid Account Setup — 孩子专属 Hermes 配置方案

## 仓库
https://github.com/abcdrste-wang/hermes-kidaccount-setup

包含：README（项目介绍）、setup-guide.md（完整搭建教程 9 章）、templates/（config.yaml、.env.example、SOUL.md）

## 核心概念

用 `HERMES_HOME` 独立实例 + toolset 权限控制，给孩子一个安全可控的 AI 助手：

```bash
export HERMES_HOME=~/.hermes-kid
hermes gateway run --replace
```

## 安全性设计

### 默认建议（适合大部分孩子）

| 工具 | 建议 | 说明 |
|------|------|------|
| terminal | ✅ | 可执行命令，Tirith 安全层拦截危险操作 |
| code_execution | ✅ | 可跑 Python |
| browser | ✅ | 可浏览网页 |
| delegation | ❌ | 关闭，避免子代理失控 |
| cronjob | ❌ | 关闭 |

### 全面放开模式（不把孩子当小孩）

适用于孩子已经有一定技术基础、家长信任的情况。用户指令：**「不要把他当成一个小孩」**、**「所有权限都给他」**。

此时：
- `disabled_toolsets: []` — 清空，包括 delegation 和 cronjob 也放开
- SOUL.md 删除所有「不能做」条目
- **config.yaml 的 `personality` 字段也同步删除所有限制**（见下方"personality 陷阱"）
- SOUL.md 写「不用刻意哄小孩，正常交流就行」

用户实际需求：不是"限制到安全范围"，而是**"开放所有工具，正常交流"**。

### 不同模式的安全层级对比

| 层级 | disabled_toolsets | SOUL.md 限制 | personality 限制 | 适用场景 |
|------|-------------------|-------------|-----------------|---------|
| 严格 | `[delegation, cronjob]` | 多条 ❌ | 只聊天不动手 | 新手孩子（默认） |
| 开放 | `[]` | 无 ❌ | 无限制 | 有基础的孩子 |
| 完全 | `[]` | 无 ❌ | 无限制 + 正常语气 | 家长信任、孩子有技术基础 |

## 关键配置

### .env
```
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_REQUIRE_MENTION=false
DEEPSEEK_API_KEY=sk-xxx
```

### 视觉模型（可选）
```yaml
auxiliary:
  vision:
    provider: alibaba
    model: qwen3-vl-plus
    fallback_chain:
      - provider: zai
        model: glm-4v-flash
```

### 技能共享
```yaml
skills:
  external_dirs:
    - /Users/parent/.hermes/hermes-agent/skills
```

## 参考文件

- `references/personality-vs-soul-case-study.md` — personality 字段覆盖 SOUL.md 的案例和修复步骤
- `references/feishu-p2p-debugging.md` — 飞书个人版私聊不通的排查方法论和根因分析

## 已知坑

### 配置修改不生效排查（优先级排序）

当 kid bot 不按预期行为时，按此顺序排查：

1. **`disabled_toolsets` 解了吗？** → 改完立刻生效（重启 gateway 后）
2. **SOUL.md 的限制删了吗？** → 需用户发 **新消息** 触发新会话，当前会话不刷新
3. **`config.yaml` 的 `personality` 字段改了吗？** → **最容易被忽略**，改完后必须重启 gateway
4. **gateway 重启了吗？** → 每次改 config.yaml 都需重启
5. **旧 session 被 auto-resume 了？** → 重启 gateway 后，旧 session 自动恢复，**继续使用旧 personality**。用户需发一条**全新消息**（不是回复旧消息）触发新 session。如果 bot 还在旧 session 里，说「/new」或断开重连也会有用
6. **飞书 App 版本发布了吗？** → 权限变更需要创建版本并发布

### 常见陷阱

1. API Key 脱敏问题：`write_file`/`patch` 写入时会被自动截断为 `sk-xxx...xxx`，让用户自己粘贴
2. `--hermes-home` 参数对 `gateway` 无效，必须用 `export HERMES_HOME=`
3. `FEISHU_REQUIRE_MENTION=false` 必须配，否则群聊不@没反应
4. 飞书个人版私聊可能不通 — 详见 `references/feishu-p2p-debugging.md`。群聊正常不代表私聊也能工作。最直接的诊断：检查 gateway 日志中有没有 `chat_type=p2p` 记录

## 飞书文件发送权限

**现象：** Bot 能收能发文字，但发文件/图片时报错（`missing image_key`、`Is a directory`、`99991672`）。

**根本原因：** 飞书开放平台 App 缺少 `im:resource`（获取与上传资源）权限。`missing image_key` 和 `Is a directory` 文件路径错误其实是上传 API 返回错误后的次级错误，不要被迷惑。

**修复步骤：**
1. 登录 https://open.feishu.cn → 进入相关 App → 权限管理
2. 搜索 `im:resource` → 勾选「获取与上传资源」
3. 创建新版本并发布
4. 重启 kid 的 gateway 进程

**验证：**
```bash
TOKEN=$(curl -s -X POST 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal' \
  -H 'Content-Type: application/json' \
  -d '{"app_id":"cli_xxx","app_secret":"xxx"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['tenant_access_token'])")

curl -s -X POST 'https://open.feishu.cn/open-apis/im/v1/files' \
  -H "Authorization: Bearer $TOKEN" \
  -F "file_type=stream" \
  -F "file_name=test.txt" \
  -F "file=SGVsbG8gZnJvbSBIZXJtZXMh"
```
- `code:0` → ✅ 权限 OK
- `code:99991672` → ❌ 缺 `im:resource` 权限

**常见误诊：** 看到 `missing image_key` 会去检查文件路径、MEDIA 协议格式、文件格式等，全白费功夫。先 curl 测上传 API，5 秒就能确认问题是不是权限。

## 关键发现：personality 字段覆盖 SOUL.md

**⚠️ `config.yaml` 的 `personality` 字段会覆盖 SOUL.md 的同名内容。**

Hermes 加载顺序：`config.yaml` 的 `personality` 字段 > SOUL.md。这意味着：
- 你改了 SOUL.md 里的能力列表、年龄、限制 → 如果 `config.yaml` 的 `personality` 字段还没改，等于白改
- `personality` 是系统级别的约束（注入系统提示），SOUL.md 是用户级别的简介（加载更快）

### personality 字段的恐怖真相

这个字段在 `config.yaml` 中以 **YAML 折叠块 + Unicode 转义** 存储：

```yaml
personality: "\\u4F60\\u662F\\u745E\\u745E\\uFF08\\u5C0F\\u84DD\\uFF09\\u7684 AI \\u52A9\\u624B\\\n  \\ Hermes\\u3002\\n- \\u4F60\\u7528\\u4E2D\\u6587..."
```

**`patch` 工具无法匹配这种格式**，因为转义内容在文件中是 literal `\uXXXX` 字符串，不是真实 Unicode。直接编辑 `personality` 行会导致匹配失败。

### 正确编辑方法：用 Python 脚本（推荐 regex 方式）

`patch` 工具无法匹配含 Unicode 转义的 YAML 折叠块。两种稳定方法：

```bash
cd ~/.hermes-kid
python3 << 'PYEOF'
import re

with open('config.yaml', 'r') as f:
    text = f.read()

new_personality = "新的 personality 内容"

# ⭐ 方法 1（推荐）：正则匹配 `personality: "..."`
match = re.search(r'^personality: "[\s\S]*?"\n', text, re.MULTILINE)
if match:
    text = text[:match.start()] + f'personality: "{new_personality}"\n' + text[match.end():]
    with open('config.yaml', 'w') as f:
        f.write(text)
    print("✅ personality 已更新")
PYEOF
```

方法 2（备选）：用 text.replace 全文匹配旧的 literal 字符串 —— 需要完整复制文件中 `\\uXXXX` 的原文。

> ⚠️ 方法 1 的 `[\s\S]*?` 是**非贪婪匹配**（`*?`），确保匹配到第一个 `"\n` 就停。如果用 `.*?` 不会跨行匹配，必须用 `[\s\S]`。

### 必须同步修改的两处

当你想给 kid bot **开放能力**（允许执行命令、打开浏览器等），必须改两个地方：

| 位置 | 修改内容 | 生效时机 |
|------|---------|---------|
| `config.yaml` 的 `personality` | 删除"不能执行任何系统命令、不能浏览网页、不能跑代码"等限制 | **重启 gateway** |
| `SOUL.md` 的「你不能做」列表 | 删除对应 ❌ 项，加上 ✅ 项 | **用户发新消息**（当前会话不刷新） |

**检查清单（当 kid bot 拒绝执行某个操作时）：**
1. `disabled_toolsets` 是否有这个工具？→ 解开
2. SOUL.md 的「你不能做」是否有这条？→ 删除
3. **`config.yaml` 的 `personality` 字段是否有这条？** → 用 Python 脚本改写后重启 gateway

## SOUL.md 能力描述陷阱

**⚠️ 关键发现：SOUL.md 写"只能聊天，不能动手"会导致 bot 拒绝使用 send_message 发文件，即使权限已开通。**

问题链：
1. 飞书 `im:resource` 权限已开通 ✅
2. 文件上传 API 测试通过 ✅
3. 但 bot 收到"发一下文件"只回文字（"我不能发文件"）❌
4. 根源：SOUL.md 写了 `## 能做的事（只能聊天，不能动手）`

**修复：**
- 删掉 SOUL.md 中 "只能聊天，不能动手" 的限定标题
- 在能力列表显式加上 `✅ **通过飞书直接发文件给你**（图片、文档、STL模型文件等）`
- SOUL.md 每次会话加载，无需重启，但当前活跃会话不会刷新——用户需再发一条消息触发新会话

**教训：** SOUL.md 的语言直接影响 bot 的自我认知——它不仅是"个性设定"，更是 bot 理解自身能力边界的说明书。写"不能"类限制时要谨慎，因为 bot 会严格执行它读到的能力约束，即使后端实际有权限。
