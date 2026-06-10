#!/bin/bash
# Mac Mini - 一键配置下载加速环境
# 贴在 Mac 终端里跑

set -e

echo "=== 1. 配置 npm/pnpm 国内镜像源 ==="
npm config set registry https://registry.npmmirror.com
pnpm config set registry https://registry.npmmirror.com
echo "✅ npm 镜像源已设为 npmmirror.com"

echo ""
echo "=== 2. 配置 Xray 代理环境变量 ==="
echo 'export all_proxy=socks5://127.0.0.1:10808' >> ~/.zshrc
echo 'export http_proxy=http://127.0.0.1:10809' >> ~/.zshrc
echo 'export https_proxy=http://127.0.0.1:10809' >> ~/.zshrc
source ~/.zshrc
echo "✅ 代理环境变量已写入 ~/.zshrc"

echo ""
echo "=== 3. 克隆 html-video（走代理） ==="
cd ~
all_proxy=socks5://127.0.0.1:10808 \
  git clone --depth 1 https://github.com/nexu-io/html-video.git
echo "✅ html-video 已克隆"

echo ""
echo "=== 4. 安装依赖（镜像源 + 跳过 Chromium） ==="
cd ~/html-video
PUPPETEER_SKIP_DOWNLOAD=true \
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
  pnpm install
echo "✅ npm 依赖已安装"

echo ""
echo "=== 5. 单独下载 Chromium（走代理，自动重试） ==="
echo "下载中，大概 300MB，请耐心等待..."
all_proxy=socks5://127.0.0.1:10808 \
  npx @puppeteer/browsers install chrome@stable 2>&1 | tail -3
echo "✅ Chromium 已下载"

echo ""
echo "🎉 全部搞定！试试渲染："
echo "  cd ~/html-video"
echo '  all_proxy=socks5://127.0.0.1:10808 npx html-video render ...'
