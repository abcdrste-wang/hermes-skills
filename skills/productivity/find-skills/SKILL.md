---
name: find-skills
description: 帮你把需求翻译成技能组合——当你不知道装什么 skill 时，告诉它你要做什么，它会推荐合适的 skills
---

# find-skills

当你面对一个问题但不确定该装什么 Hermes Skill 时，用这个 skill。

## 使用方式

直接描述你的需求，我会推荐最适合的技能组合。

## 你有哪些 skill 可用

以下是当前已安装的主要 skills，按场景分类：

### 📋 项目管理与生产力
- **plan** — 复杂任务先写计划再执行
- **obsidian** — 读写 Obsidian 笔记
- **google-workspace** — Gmail/Calendar/Drive/Docs
- **linear** — 管理 issue/project
- **notion** — Notion 页面和数据库操作
- **excel-spreadsheets** — Excel 文件读写
- **nano-pdf** — PDF 文本编辑
- **ocr-and-documents** — PDF/扫描件文字提取
- **pdf-generation** — PDF 生成（fpdf2/reportlab）

### 🎨 设计与内容创作
- **excalidraw** — 手绘风格流程图/架构图
- **claude-design** — HTML 设计原型
- **sketch** — 快速 HTML 设计对比
- **architecture-diagram** — 深色主题 SVG 架构图
- **p5js** — 生成艺术/交互式 3D 草图
- **pixel-art** — 像素艺术（NES/Game Boy/PICO-8 色板）
- **ascii-art** — ASCII 艺术字/图形
- **design-md** — DESIGN.md 规范文件
- **baoyu-comic / baoyu-infographic / baoyu-article-illustrator** — 信息图/漫画/文章配图
- **claude-design** — 一次性设计原型

### 📝 内容发布
- **content-publishing** — 文章配图/排版/发布全流程
- **ai-content-publishing** — AI 生成中文内容并发布
- **wechat-official-account** — 微信公众号内容指南
- **humanizer** — 去 AI 味、加入真实语气

### 🔬 开发与工程
- **github-pr-workflow** — PR 全流程管理
- **github-code-review** — 代码审查
- **github-issues** — Issue 创建与管理
- **github-repo-management** — 仓库管理
- **codebase-inspection** — 代码库结构分析（pygount）
- **test-driven-development** — TDD 红绿重构循环
- **systematic-debugging** — 4 阶段根因调试
- **requesting-code-review** — 提交前安全检查
- **spike** — 快速实验验证想法
- **writing-plans** — 编写实现计划
- **codex** — 委托 Codex CLI 编程
- **claude-code** — 委托 Claude Code CLI

### 🚀  DevOps 与基础设施
- **china-network-environment** — 国内网络环境配置
- **gfw-bypass-proxy** — Xray 代理配置
- **xray-proxy-setup** — Xray VLESS 客户端配置
- **restricted-network-install** — 受限网络环境安装
- **hermes-server-ops** — Hermes 服务器运维
- **hermes-provider-config** — LLM Provider 配置
- **hermes-feishu-lark-cli** — 飞书 CLI 绑定配置
- **hermes-feishu-bot-troubleshooting** — 飞书 Bot 排错
- **webhook-subscriptions** — Webhook 事件订阅
- **codex-deepseek-gateway** — Codex + DeepSeek 网关配置

### 🤖 AI/ML
- **llama-cpp** — 本地 GGUF 推理
- **serving-llms-vllm** — vLLM 高吞吐推理
- **huggingface-hub** — HF 模型/数据集搜索下载
- **context-compression** — Token 压缩评估
- **headroom-mcp-integration** — Headroom MCP Token 压缩
- **apple-silicon-local-llm** — Mac M 系列本地 LLM
- **gemini-free-vision** — Google Gemini 免费视觉
- **segment-anything-model** — SAM 零样本图像分割
- **audiocraft-audio-generation** — 音乐/音效生成
- **comfyui** — ComfyUI 图像/视频/音频生成
- **dspy** — 声明式 LM 编程
- **evaluating-llms-harness** — lm-eval-harness 基准测试
- **weights-and-biases** — W&B 实验追踪
- **minimax-hailuo-video** — MiniMax 海螺 AI 视频生成

### 📊 数据与调研
- **deep-research** — 多角度深度调研
- **arxiv** — arXiv 论文搜索
- **research-investigation** — 高效技术调研
- **web-scraping** — 网页抓取（静态/动态）
- **wechat-article-research** — 微信公众号文章调研
- **blogwatcher** — RSS/Blog 订阅监控
- **sentiment-monitoring** — 舆情监控
- **data-analytics-reporter** — 数据分析与报告
- **jupyter-live-kernel** — 交互式 Jupyter 数据分析

### 🛒 电商与比价
- **taobao-jd-pricer** — 淘宝/京东比价
- **12306-query** — 12306 余票查询

### 🧪 测试与质量
- **dogfood** — Web 应用探索性 QA
- **testing-api-tester** — API 测试
- **testing-accessibility-auditor** — 无障碍审计
- **testing-performance-benchmarker** — 性能基准测试
- **testing-reality-checker** — 集成冒烟测试
- **testing-evidence-collector** — 测试证据收集
- **testing-workflow-optimizer** — 工作流优化
- **testing-tool-evaluator** — 工具评估

### 📧 通讯与社交
- **himalaya** — 终端邮件（IMAP/SMTP）
- **xurl** — X/Twitter 发帖搜索私信
- **spotify** — Spotify 音乐控制
- **polymarket** — Polymarket 预测市场查询

### 📹 视频与媒体
- **manim-video** — 3Blue1Brown 风格数学动画
- **songwriting-and-ai-music** — 写词 + Suno AI 音乐
- **youtube-content** — YouTube 视频摘要
- **gif-search** — Tenor GIF 搜索下载
- **text-to-speech** — 文字转语音
- **songsee** — 音频频谱可视化

### 🌐 飞书（Lark）集成
- **lark-im** — 飞书即时通讯
- **lark-doc** — 飞书文档读写
- **lark-wiki** — 飞书知识库
- **lark-sheets** — 飞书电子表格
- **lark-base** — 飞书多维表格
- **lark-task** — 飞书任务管理
- **lark-calendar** — 飞书日历与会议室
- **lark-contact** — 飞书通讯录
- **lark-drive** — 飞书云空间
- **lark-approval** — 飞书审批
- **lark-attendance** — 飞书考勤
- **lark-okr** — 飞书 OKR
- **lark-mail** — 飞书邮箱
- **lark-minutes** — 飞书妙记
- **lark-vc** — 飞书视频会议
- **lark-vc-agent** — 飞书会议机器人代参会
- **lark-slides** — 飞书幻灯片
- **lark-whiteboard** — 飞书画板
- **lark-event** — 飞书事件监听
- **lark-markdown** — 飞书 Markdown 文件
- **lark-skill-maker** — 封装飞书 API 为 Skill
- **lark-openapi-explorer** — 飞书原生 OpenAPI 探索
- **lark-workflow-meeting-summary** — 会议纪要整理
- **lark-workflow-standup-report** — 日程待办摘要

### 🏠 智能家居
- **openhue** — Philips Hue 灯光控制

## 推荐原则

1. **按需组合** — 复杂场景通常需要 2-3 个 skill 协作
2. **先核心后扩展** — 先装最核心的一个，再根据需要补充
3. **避免功能重叠** — 比如 web-scraping 和 scrapling 选一个即可
4. **优先内置 skill** — 内置的优先于外部安装的
5. **不要替用户过滤** — 永远假设用户的场景比你想象的多。如果你觉得某个 skill "增量价值不大"，先不下结论，直接列出来让用户决定

## Pitfalls

- **不要过早否定** — 用户说 "我们的场景并不固定" 。不要因为你对用户的现有了解（如内容管线）就认为其他 skill 不相关。用户可能随时有新品种的需求（3D 打印、数据分析、IoT...），保持开放

## 使用示例

- "我想定时抓取一个竞品网站的价格数据，每天早上发给我"
  → 推荐: scrapling + cronjob + excel-spreadsheets（或 google-workspace）
- "我需要做一个产品技术文档的网站"
  → 推荐: content-publishing + architecture-diagram + excalidraw
- "我想分析飞书群里过去一个月的讨论热点"
  → 推荐: lark-im（搜索聊天记录）+ lark-workflow-meeting-summary

## 更多场景

详细的使用场景案例见 `references/use-cases.md`（开发者、内容创作、数据采集、基础设施、飞书自动化、AI/ML、视频媒体共 7 大类 20+ 场景）。
