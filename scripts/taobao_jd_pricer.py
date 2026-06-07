#!/usr/bin/env python3
"""
淘宝 × 京东 比价脚本
---
用法:
  python3 taobao_jd_pricer.py login     # 首次扫码登录（淘宝 + 京东）
  python3 taobao_jd_pricer.py search "关键词"  # 搜索比价
  python3 taobao_jd_pricer.py search "关键词" --limit 5  # 每平台取前5个商品

首次使用:
  1. python3 taobao_jd_pricer.py login
  2. 浏览器窗口弹出 → 手动扫码登录淘宝 → 然后扫码登录京东
  3. 登录成功后 Cookie 自动保存
  4. 后续直接 python3 taobao_jd_pricer.py search "你想要的东西"

依赖: playwright (pip3 install playwright && playwright install chromium)
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

COOKIE_DIR = Path.home() / ".hermes" / "pricer_cookies"
COOKIE_DIR.mkdir(parents=True, exist_ok=True)

TAOBAO_COOKIE = COOKIE_DIR / "taobao.json"
JD_COOKIE = COOKIE_DIR / "jd.json"

from playwright.sync_api import sync_playwright

# ── 工具函数 ──────────────────────────────────────────────

def _make_browser(p, headless=False):
    """创建隐身 Chromium 浏览器（默认非 headless，方便扫码）"""
    browser = p.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )
    return browser, context


def _save_cookies(context, path):
    """保存 Cookie 到文件"""
    cookies = context.cookies()
    path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
    print(f"  ✓ Cookie 已保存 → {path}")


def _load_cookies(context, path):
    """从文件加载 Cookie"""
    if not path.exists():
        return False
    cookies = json.loads(path.read_text())
    context.add_cookies(cookies)
    print(f"  ✓ Cookie 已加载 → {path}")
    return True


def _wait_for_login(page, url, check_selector, timeout_sec=120):
    """
    打开登录页面，等待用户手动扫码登录完成。
    check_selector: 登录成功后页面出现的选择器，用于判断登录完成。
    """
    page.goto(url, wait_until="domcontentloaded")
    print(f"  ⏳ 请在打开的浏览器窗口中扫码登录（{timeout_sec}秒超时）...")

    deadline = time.time() + timeout_sec
    logged_in = False
    while time.time() < deadline:
        try:
            page.wait_for_selector(check_selector, timeout=5000)
            logged_in = True
            break
        except Exception:
            # 还没登录成功，继续等
            pass
        time.sleep(2)

    if logged_in:
        print("  ✓ 登录成功！")
    else:
        print("  ✗ 登录超时，请重试 login 命令")
    return logged_in


def _extract_taobao_items(page, limit=10):
    """从淘宝搜索结果页提取商品信息"""
    items = []
    try:
        cards = page.query_selector_all("[class*='Card']")
        if not cards:
            cards = page.query_selector_all("[class*='item']")
        if not cards:
            cards = page.query_selector_all(".search-result-item")

        # 通用 fallback: 取所有带有价格 class 的父容器
        if not cards:
            price_els = page.query_selector_all("[class*='price']")
            seen = set()
            for el in price_els[:limit * 3]:
                parent = el.evaluate("el => el.closest('[class*=\"item\"],[class*=\"Card\"],[class*=\"card\"]')")
                if parent and parent not in seen:
                    cards.append(parent)
                    seen.add(parent)

        for card in cards[:limit]:
            try:
                title = card.inner_text()[:80].replace("\n", " | ").strip()
            except Exception:
                title = "N/A"

            try:
                price_el = card.query_selector("[class*='price']")
                price = price_el.inner_text().strip() if price_el else "N/A"
            except Exception:
                price = "N/A"

            try:
                shop_el = card.query_selector("[class*='shop']")
                shop = shop_el.inner_text().strip() if shop_el else "N/A"
            except Exception:
                shop = "N/A"

            try:
                sales_el = card.query_selector("[class*='sales'],[class*='deal']")
                sales = sales_el.inner_text().strip() if sales_el else "N/A"
            except Exception:
                sales = "N/A"

            try:
                link_el = card.query_selector("a[href*='item']")
                link = "https:" + link_el.get_attribute("href") if link_el else "N/A"
            except Exception:
                link = "N/A"

            items.append({
                "title": title,
                "price": price,
                "shop": shop,
                "sales": sales,
                "link": link,
            })
    except Exception as e:
        print(f"  ⚠ 淘宝解析异常: {e}")

    return items


def _extract_jd_items(page, limit=10):
    """从京东搜索结果页提取商品信息"""
    items = []
    try:
        # 京东经典商品列表
        goods = page.query_selector_all(".gl-item")
        if not goods:
            goods = page.query_selector_all("[class*='item']")
        if not goods:
            # 新版本京东
            goods = page.query_selector_all("[class*='goods-item']")

        for good in goods[:limit]:
            try:
                title_el = good.query_selector(".p-name a em")
                if not title_el:
                    title_el = good.query_selector("[class*='name']")
                title = title_el.inner_text().strip() if title_el else "N/A"
            except Exception:
                title = "N/A"

            try:
                price_el = good.query_selector(".p-price i")
                if not price_el:
                    price_el = good.query_selector("[class*='price']")
                price = price_el.inner_text().strip() if price_el else "N/A"
            except Exception:
                price = "N/A"

            try:
                shop_el = good.query_selector(".p-shop a")
                if not shop_el:
                    shop_el = good.query_selector("[class*='shop']")
                shop = shop_el.get_attribute("title") or shop_el.inner_text().strip() if shop_el else "N/A"
            except Exception:
                shop = "N/A"

            try:
                commit_el = good.query_selector(".p-commit a")
                if not commit_el:
                    commit_el = good.query_selector("[class*='commit']")
                commit = commit_el.inner_text().strip() if commit_el else "N/A"
            except Exception:
                commit = "N/A"

            try:
                link_el = good.query_selector(".p-name a")
                href = link_el.get_attribute("href") if link_el else ""
                link = f"https:{href}" if href and href.startswith("//") else href or "N/A"
            except Exception:
                link = "N/A"

            items.append({
                "title": title,
                "price": price,
                "shop": shop,
                "sales": commit,
                "link": link,
            })
    except Exception as e:
        print(f"  ⚠ 京东解析异常: {e}")

    return items


# ── 核心命令 ──────────────────────────────────────────────

def cmd_login():
    """首次扫码登录淘宝+京东"""
    print("=" * 60)
    print("  淘宝 & 京东 首次登录")
    print("  将依次弹出两个浏览器窗口，请分别扫码登录")
    print("  Cookie 会自动保存，后续无需重复登录")
    print("=" * 60)

    with sync_playwright() as p:
        # ── 淘宝 ──
        print("\n--- 步骤 1/2: 淘宝登录 ---")
        browser, context = _make_browser(p)
        page = context.new_page()

        ok = _wait_for_login(
            page,
            "https://login.taobao.com/",
            check_selector=".site-nav-login-info-nick",  # 登录后头像/昵称区域
            timeout_sec=120,
        )
        if ok:
            time.sleep(2)
            _save_cookies(context, TAOBAO_COOKIE)
        browser.close()

        # ── 京东 ──
        print("\n--- 步骤 2/2: 京东登录 ---")
        browser, context = _make_browser(p)
        page = context.new_page()

        ok = _wait_for_login(
            page,
            "https://passport.jd.com/",
            check_selector=".nickname",  # 登录后的昵称
            timeout_sec=120,
        )
        if ok:
            time.sleep(2)
            _save_cookies(context, JD_COOKIE)
        browser.close()

    print("\n✅ 登录完成！可以开始比价了：")
    print('   python3 taobao_jd_pricer.py search "你想要的关键词"')


def cmd_search(keyword: str, limit: int = 10, dryrun: bool = False):
    """搜索关键词并比价"""
    mode = "（无登录，仅测试连通性）" if dryrun else ""
    print(f"\n🔍 搜索: 「{keyword}」 (各取前 {limit} 条) {mode}\n")

    results = {"淘宝": [], "京东": []}

    with sync_playwright() as p:
        # ── 淘宝 ──
        print("─── 淘宝 ───")
        browser, context = _make_browser(p, headless=True)
        if not _load_cookies(context, TAOBAO_COOKIE) and not dryrun:
            print("  ✗ 未找到淘宝 Cookie，请先运行 login 命令")
            browser.close()
            return

        page = context.new_page()
        try:
            search_url = f"https://s.taobao.com/search?q={keyword}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)  # 等待前端渲染
            print(f"  → 页面标题: {page.title()}")

            items = _extract_taobao_items(page, limit)
            results["淘宝"] = items
            print(f"  → 抓取到 {len(items)} 个商品")
        except Exception as e:
            print(f"  ✗ 淘宝搜索失败: {e}")
        finally:
            browser.close()

        # ── 京东 ──
        print("\n─── 京东 ───")
        browser, context = _make_browser(p, headless=True)
        if not _load_cookies(context, JD_COOKIE) and not dryrun:
            print("  ✗ 未找到京东 Cookie，请先运行 login 命令")
            browser.close()
            return

        page = context.new_page()
        try:
            search_url = f"https://search.jd.com/Search?keyword={keyword}&enc=utf-8"
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            print(f"  → 页面标题: {page.title()}")

            items = _extract_jd_items(page, limit)
            results["京东"] = items
            print(f"  → 抓取到 {len(items)} 个商品")
        except Exception as e:
            print(f"  ✗ 京东搜索失败: {e}")
        finally:
            browser.close()

    # ── 输出对比表格 ──
    print("\n" + "=" * 80)
    print(f"📊 比价结果：{keyword}")
    print("=" * 80)
    for platform, items in results.items():
        print(f"\n【{platform}】")
        if not items:
            print("  (无数据)")
            continue
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item['title'][:60]}")
            print(f"     价格: {item['price']:>15}   店铺: {item['shop']}")
            if item.get("sales"):
                print(f"     销量: {item['sales']}")
            if item.get("link") and item["link"] != "N/A":
                print(f"     链接: {item['link']}")
            print()

    print("=" * 80)

    # 简单比价提示
    tb_prices = []
    for item in results.get("淘宝", []):
        if item["price"] != "N/A":
            try:
                p = item["price"].replace("¥", "").replace("￥", "").strip()
                tb_prices.append(float(p.split()[0]))
            except:
                pass
    jd_prices = []
    for item in results.get("京东", []):
        if item["price"] != "N/A":
            try:
                p = item["price"].replace("¥", "").strip()
                jd_prices.append(float(p.split()[0]))
            except:
                pass

    if tb_prices and jd_prices:
        tb_avg = sum(tb_prices) / len(tb_prices)
        jd_avg = sum(jd_prices) / len(jd_prices)
        diff = ((jd_avg - tb_avg) / tb_avg) * 100
        print(f"\n💰 价格对比（均价）:")
        print(f"   淘宝均价: ¥{tb_avg:.2f} ({len(tb_prices)}条)")
        print(f"   京东均价: ¥{jd_avg:.2f} ({len(jd_prices)}条)")
        if diff > 0:
            print(f"   京东贵 {diff:.1f}%")
        elif diff < 0:
            print(f"   京东便宜 {abs(diff):.1f}%")
        else:
            print(f"   价格持平")


# ── 入口 ──────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="淘宝 × 京东 比价工具")
    parser.set_defaults(func=lambda args: parser.print_help())
    sub = parser.add_subparsers(dest="command")

    login_parser = sub.add_parser("login", help="首次扫码登录淘宝+京东")
    login_parser.set_defaults(func=lambda args: cmd_login())

    search_parser = sub.add_parser("search", help="搜索比价")
    search_parser.add_argument("keyword", type=str, help="搜索关键词")
    search_parser.add_argument("--limit", type=int, default=5, help="每平台取前N条 (默认5)")
    search_parser.add_argument("--dryrun", action="store_true", help="忽略Cookie，不登录直接搜索（仅供远程测试连通性）")
    search_parser.set_defaults(func=None)  # 手动处理

    args = parser.parse_args()

    if args.command == "login":
        cmd_login()
    elif args.command == "search":
        cmd_search(args.keyword, limit=args.limit, dryrun=args.dryrun)
    else:
        parser.print_help()
