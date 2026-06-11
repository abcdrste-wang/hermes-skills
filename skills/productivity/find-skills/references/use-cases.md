# find-skills: Use Case Reference

Common real-world scenarios mapped to Hermes skill combinations.
Based on community experience and the 丁卯生人 skill series.

## Developer Workflows

### "我写完代码想提 PR，但不想手动写描述"
→ `github-pr-workflow` (built-in)
  Hermes 自动生成 commit message + PR 描述 + @ reviewer

### "我想做代码审查"
→ `github-code-review` + `requesting-code-review`
  先安全检查，再行内审查

### "代码库太大了，我想看清结构"
→ `codebase-inspection` (pygount)
  分析文件数、语言分布、代码比例

### "我想先写计划再执行"
→ `plan` (built-in)
  /plan 模式，先出 markdown 计划，确认后再动手

## Content & Publishing

### "我要写一篇公众号文章"
→ `ai-content-publishing` + `content-publishing` + `humanizer`
  调研→写稿→配图→去AI味→发布

### "我要画一个流程图"
→ `excalidraw`
  30 秒生成手绘风格流程图/架构图

### "我要做一个信息图"
→ `baoyu-infographic` 或 `architecture-diagram`
  前者信息图风格，后者深色主题技术架构图

## Data Collection & Monitoring

### "我想定时抓取竞品价格，每天早上发给我"
→ `scrapling` (or `web-scraping`) + cron + `excel-spreadsheets`
  combo: scrapling 绕过反爬 → cron 定时 → excel 整理

### "我想监控某个话题的舆情"
→ `blogwatcher` + `sentiment-monitoring` + cron
  RSS/Blog 订阅监控 + 情感分析

### "我想每天早上看 AI 圈新闻"
→ cron + `web_search` (built-in tool) 
  免费，无需 API Key，每天定时搜关键词汇总

## Infrastructure

### "Docker 命令记不住"
→ Docker management skill (if available)
  自然语言转 docker 命令，先预览再执行

### "Hermes 出问题了不知道怎么排查"
→ `hermes-server-ops` + `hermes-feishu-bot-troubleshooting`
  服务器运维 + Bot 排错

## Feishu/Lark Automation

### "我想分析飞书群聊天热点"
→ `lark-im` (搜索消息记录) + `lark-workflow-meeting-summary`

### "我想定时导出飞书文档"
→ `lark-doc` + `lark-drive` + cron

## AI/ML Work

### "我想跑个本地 LLM"
→ `llama-cpp` + `apple-silicon-local-llm` (Mac) or `huggingface-hub`
  下载模型 → 本地推理

### "我想给 LLM 做 benchmark"
→ `evaluating-llms-harness`
  MMLU/GSM8K 等标准评测

## Video & Media

### "我想把数学算法做成视频"
→ `manim-video`
  3Blue1Brown 风格动画

### "我想用提示词生成歌曲"
→ `songwriting-and-ai-music`
  写词 + Suno AI 音乐生成

### "我想把公众号文章转成视频"
→ `minimax-hailuo-video`
  分镜头脚本 → 多段视频 → ffmpeg 拼接
