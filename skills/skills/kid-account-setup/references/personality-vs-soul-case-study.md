# Personality 字段 vs SOUL.md 冲突案例

## 场景（2026-06-09 瑞瑞机器人调优）

用户发现瑞瑞的飞书 bot 无法执行命令、无法打开浏览器、无法发文件，即使：
- `disabled_toolsets` 已解除对 terminal/code_execution/browser 的限制
- 飞书 `im:resource` 权限已开通
- 文件上传 API 测试通过

## 排查过程

1. 检查 `disabled_toolsets` → ✅ 已解禁
2. 检查 SOUL.md → ✅ 「不能动手」标题已删，能力列表已加 ✅ 
3. **检查 `config.yaml` 的 `personality` 字段 → ❌ 发现旧版限制！**

## 根因

`config.yaml` 的 `personality` 字段在加载时 **覆盖** SOUL.md 的同名内容。旧版内容：

```yaml
personality: "你是瑞瑞（小蓝）的 AI 助手 Hermes。
- 瑞瑞今年8岁
- 你不能执行任何系统命令、不能浏览网页、不能跑代码、不能委托给别人做
- 你只能动嘴（聊天），不能动手（操作电脑）"
```

尽管 SOUL.md 已修改，但 personality 中的「不能动手」约束仍在系统提示层面生效，导致 bot 自我认知为「只能聊天」。

## 修复步骤（已验证工作流）

### 完全解禁一个 kid bot 的步骤

```
1. 编辑 config.yaml  → 清空 disabled_toolsets 为 []
2. 编辑 config.yaml  → 用 Python regex 改写 personality 字段（删除所有限制）
3. 编辑 SOUL.md     → 删除「你不能做」列表，添加「你能做」列表
4. 重启 gateway     → hermes gateway run --replace
5. 用户发新消息     → 触发新 session（/new 或完全新消息）
```

### 验证步骤

```
1. hermes doctor                → 检查全局配置
2. 直接 API 测试文件上传        → curl 测 im/v1/files
3. 直接 API 测试文件发送到群    → curl 测 im/v1/messages
4. 在群里对 bot 说"发个文件"   → 看日志确认 bot 的回复
```

## 经验教训

1. 用 Python 脚本（推荐 regex 方法）替换 config.yaml 中的 personality 字段
2. 同步更新 SOUL.md 的「不能做」列表
3. 重启 gateway 使新 config.yaml 生效

## 全面放开模式（2026-06-09 第二波改进）

用户后续指令：**「把这些限制全都打开，包括终端的命令都给他，权限都给他。不要把他当成一个小孩」**

此轮修改：
1. `disabled_toolsets: []` — 连 delegation 和 cronjob 也清空
2. `personality` 改为「没有能力限制，所有工具都可以使用」
3. SOUL.md 删除全部「你不能做」列表，只剩「不能替你做作业」

### 关键细节

被 personality 限制过的 bot 会形成**行为惯性**——即使限制解除了，当前会话仍表现为"只聊天不动手"。需要：
- 重启 gateway（让新 config.yaml 加载）
- 用户发 **新消息** 触发新会话（让新 personality 注入到系统提示）
- 不需要重新部署飞书 App

## 经验教训

- 修改 bot 能力限制时，**必须检查 3 个位置**：`disabled_toolsets` → SOUL.md → config.yaml personality
- `personality` 是 3 个位置中**优先级最高**的（系统提示层），改了前两个没改它等于白改
- `patch` 工具不能编辑包含 Unicode 转义的 YAML 折叠块，要用 Python 脚本（regex `r'^personality: "[\s\S]*?"\n'` 最稳）
- SOUL.md 修改后当前活跃会话不刷新，需要用户发新消息
- config.yaml personality 修改后需要重启 gateway
- **「全面放开」和「默认限制」是两套不同的配置基线**，用户孩子长大后或信任度提高时，可以直接切换到开放模式
