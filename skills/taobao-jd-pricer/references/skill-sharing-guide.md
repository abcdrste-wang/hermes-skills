# 分享此技能给另一个 Hermes

## 前提

对方也需要是 Hermes 用户（已安装 Playwright），并且有一台**带显示器的电脑**（首次登录需要扫码）。

## 对方需要的东西

| 资源 | 说明 |
|------|------|
| GitHub 仓库 | `https://github.com/abcdrste-wang/hermes-china-skills`（专用洁净仓库，仅包含中国区域技能） |
| 代理 | 中国网络下需要 V2rayU 或类似代理才能克隆 GitHub |
| Python 3 + Playwright | 对方 Hermes 环境已经装好 |

## 还有更多技能可以找

你俩不是唯一写 Hermes 技能的人。社区里还有一批公开的技能源：

### 1. SkillDock（技能市场，188+ 技能）

**https://skilldock.io/trending**

Hermes 和 OpenClaw 都能用的开放技能市场，有 SEO、视频编辑、落地页、后端开发、股票行情（longbridge）等技能。点「Copy for Agent」直接复制安装代码。

### 2. awesome-hermes-agent（精选列表，⭐3.7k）

**https://github.com/0xNyk/awesome-hermes-agent**

Hermes 社区收集的最全技能/工具/资源列表，按分类整理。在 GitHub 上看 README 即可。

### 3. skill-factory（自动生成技能，⭐354）

**https://github.com/Romanescu11/hermes-skill-factory**

元技能：你干活时它看着你的操作，自动帮你生成可复用的 SKILL.md。以后不用手写技能了。

### 4. self-evolution（官方自进化，⭐3.9k）

**https://github.com/NousResearch/hermes-agent-self-evolution**

Hermes 官方出品，让 Hermes 自动优化自己的技能库，去重、改进、重组。

### 5. wondelai/skills（跨平台技能合集）

**https://github.com/wondelai/skills**

产品/商业方法论类技能（clean-architecture、domain-driven-design 等），Hermes 和 Claude Code 通用。

## 安装步骤

### Step 1: 克隆仓库

在中国网络下必须用代理 + `--depth 1`（否则大仓库会 RPC 超时）：

```bash
ALL_PROXY=socks5://127.0.0.1:1080 git clone --depth 1 \
  https://github.com/abcdrste-wang/hermes-china-skills.git \
  ~/Desktop/hermes-china-skills
```

> **为什么要 `--depth 1`：** 完整克隆在大文件多的仓库上可能遇到 `RPC failed; curl 18 Transferred a partial file` 错误。`--depth 1` 只拉最新版本，够用。

### Step 2: 安装技能

```bash
# 复制比价技能
cp -r ~/Desktop/hermes-china-skills/skills/taobao-jd-pricer ~/.hermes/skills/

# 复制 12306 技能（可选，但推荐一起装）
cp -r ~/Desktop/hermes-china-skills/skills/12306-query ~/.hermes/skills/

# 复制脚本
cp ~/Desktop/hermes-china-skills/scripts/*.py ~/.hermes/scripts/

# 给脚本加执行权限
chmod +x ~/.hermes/scripts/*.py
```

### Step 3: 验证安装

```bash
ls ~/.hermes/skills/taobao-jd-pricer/       # 应看到 SKILL.md  references/
ls ~/.hermes/scripts/taobao_jd_pricer.py     # 应看到文件
```

### Step 4: 首次登录（必须在有屏幕的电脑上操作）

```bash
cd ~/.hermes/scripts
python3 taobao_jd_pricer.py login
```

会弹出 Playwright 的 Chromium 浏览器窗口，依次扫码登录淘宝和京东。完成后 Cookie 自动保存到 `~/.hermes/pricer_cookies/`。

⚠️ 这一步**不能**在 SSH 远程终端完成——需要弹出浏览器扫码。

### Step 5: 在 Hermes 中使用

在 Feishu/CLI 中直接说：
> "帮我比价 XX 商品"

Hermes 会自动加载 `taobao-jd-pricer` skill 并调用脚本。

先用 `--dryrun` 测试脚本能否正常运行（不依赖浏览器）：
```bash
python3 ~/.hermes/scripts/taobao_jd_pricer.py search "test" --limit 1 --dryrun
```

## 常见问题

### Q: `git clone` 报 `RPC failed; curl 18`

原因：大文件传输中断。解决方法已经在 Step 1 中用了 `--depth 1`。如果还不行：

```bash
# 换 HTTP 代理重试
ALL_PROXY=http://127.0.0.1:1087 git clone --depth 1 \
  https://github.com/abcdrste-wang/hermes-china-skills.git
```

### Q: Hermes 不识别这个技能

Hermes 会自动扫描 `~/.hermes/skills/`。如果识别不到：

1. 确认目录结构：`~/.hermes/skills/taobao-jd-pricer/SKILL.md`
2. 重启 Hermes
3. 在 Hermes 中说 `/skills` 查看技能列表

### Q: 怎么删除？

```bash
rm -rf ~/.hermes/skills/taobao-jd-pricer
```

脚本不影响，想删的话：`rm ~/.hermes/scripts/taobao_jd_pricer.py`

## 仓库里还有什么值得装的

| 技能 | 说明 | 需登录？|
|------|------|---------|
| `taobao-jd-pricer` | 淘宝 × 京东 比价 | 需要 |
| `12306-query` | 12306 余票查询 | 不需要 |

建议 12306 也装，零门槛，开箱即用。
