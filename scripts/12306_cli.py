#!/usr/bin/env python3
"""
12306 余票 + 票价查询（公开 API 版，无需登录）
---
用法:
  python3 12306_cli.py search "北京" "上海" 2026-06-10
  python3 12306_cli.py search "北京南" "上海虹桥" 2026-06-10 --type G
  python3 12306_cli.py search "广州南" "深圳北" 2026-06-10 --type G --seats  // 只看二等座和一等座

无需登录，无需浏览器，直接查。

依赖: 无（纯 Python 标准库）
"""

import json
import urllib.request
import argparse
from datetime import datetime

# ── 车站代码映射（从 12306 官方接口获取） ──

_STATION_CACHE = None


def _fetch_station_map():
    """从 12306 下载车站名称→代码映射"""
    global _STATION_CACHE
    if _STATION_CACHE:
        return _STATION_CACHE

    url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ✗ 获取车站列表失败: {e}")
        return {}

    import re
    m = re.search(r"var station_names\s*=\s*'([^']+)'", content)
    if not m:
        return {}

    mapping = {}
    for entry in m.group(1).split("@"):
        fields = entry.split("|")
        if len(fields) >= 5:
            # fields[1] = 中文名, fields[2] = 代码
            mapping[fields[1]] = fields[2]

    _STATION_CACHE = mapping
    return mapping


def _get_station_code(name):
    """获取车站的三字母代码"""
    mapping = _fetch_station_map()
    if name in mapping:
        return mapping[name]

    # 模糊匹配
    candidates = []
    for cn, code in mapping.items():
        if name in cn or cn in name:
            candidates.append((cn, code))
        # 也支持不带"站"的匹配（如 "北京南" 匹配 "北京南"）
        stripped = name.replace("站", "")
        if stripped == cn:
            return code

    if len(candidates) == 1:
        print(f"  ℹ 模糊匹配: '{name}' → '{candidates[0][0]}'")
        return candidates[0][1]
    elif candidates:
        print(f"  ℹ 多候选: '{name}' → {[c[0] for c in candidates]}")
        print(f"    使用 '{candidates[0][0]}'")
        return candidates[0][1]

    print(f"  ✗ 未找到车站: '{name}'")
    print(f"     试试: 北京/北京南/北京西/北京北/北京朝阳/北京丰台")
    return None


# ── 票价类型索引（根据 12306 API 返回字段位置） ──

# 12306 返回的 result 每个元素是用 | 分隔的字符串
# 关键字段索引:
#   3 = 车次
#   6 = 出发时间
#   7 = 到达时间
#   8 = 出发站代码
#   9 = 到达站代码
#   10/11 = 商务座/特等座  (有的版本不同)
# 票价信息在后面的字段中
# 更准确的方式: 从 ticket_price 接口获取

_SEAT_TYPES = [
    "商务座", "特等座", "优选一等座", "一等座", "二等座",
    "高级软卧", "软卧/动卧", "硬卧",
    "软座", "硬座", "无座",
]


def _parse_train_field(field_str, start_idx, station_map_rev):
    """解析车次信息中出发/到达站的中文名"""
    return station_map_rev.get(field_str, field_str)


def _make_station_rev(mapping):
    """反转映射: 代码→中文名"""
    return {v: k for k, v in mapping.items()}


def cmd_search(from_station, to_station, date, train_type=None, seats_only=False):
    print(f"\n🚄 查询: {from_station} → {to_station}  |  日期: {date}")

    # 获取车站代码
    mapping = _fetch_station_map()
    rev_map = _make_station_rev(mapping)

    from_code = _get_station_code(from_station)
    to_code = _get_station_code(to_station)
    if not from_code or not to_code:
        return

    # 获取出发站和到达站的中文名
    from_name = rev_map.get(from_code, from_station)
    to_name = rev_map.get(to_code, to_station)

    # 组装 API URL
    api_url = (
        f"https://kyfw.12306.cn/otn/leftTicket/queryZ?"
        f"leftTicketDTO.train_date={date}"
        f"&leftTicketDTO.from_station={from_code}"
        f"&leftTicketDTO.to_station={to_code}"
        f"&purpose_codes=ADULT"
    )

    req = urllib.request.Request(api_url)
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    # 附加 Cookie 模拟正常访问（站点/日期记忆）
    cookie = (
        f"_jc_save_fromStation=%E4%BB%8E%E5%8F%91%E7%AB%99%2C{from_code}; "
        f"_jc_save_toStation=%E5%88%B0%E8%BE%BE%E7%AB%99%2C{to_code}; "
        f"_jc_save_fromDate={date}; _jc_save_toDate={date}"
    )
    req.add_header("Cookie", cookie)

    try:
        resp = urllib.request.urlopen(req, timeout=20)
        body = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ✗ API 请求失败: {e}")
        return

    if not body.get("status"):
        print("  ✗ API 返回错误:", body.get("messages", "未知"))
        return

    raw_results = body.get("data", {}).get("result", [])
    if not raw_results:
        print("\n  ⚠ 无车次数据（可能日期太远或没有车次）")
        return

    # 解析每个车次
    trains = []
    for line in raw_results:
        fields = line.split("|")
        if len(fields) < 12:
            continue

        train_num = fields[3]

        # 筛选车次类型
        if train_type and not train_num.startswith(train_type):
            continue

        dep_time = fields[8]
        arr_time = fields[9]
        duration = fields[10]

        dep_station = rev_map.get(fields[6], fields[6])
        arr_station = rev_map.get(fields[7], fields[7])

        # 票价和余票（字段 30-46 左右变化较大，30=商务座, 31=特等座, ...）
        # 直接取关键座位类型
        seats = {}
        # 根据 12306 API 文档，座位类型字段索引:
        seat_indices = {
            "商务座": 32, "特等座": 32,  # 商务座/特等座共享字段
            "一等座": 31,
            "二等座": 30,
            "高级软卧": 21,
            "软卧/动卧": 23,
            "硬卧": 28,
            "硬座": 29,
            "无座": 26,
        }
        # 实际数据中，座位余票的索引随版本变化
        # 更稳定的做法：取 ~16 个候选字段
        seat_price_indices = {
            "商务座": 32, "特等座": 33,
            "一等座": 31,
            "二等座": 30,
            "高级软卧": 21,
            "软卧/动卧": 23,
            "硬卧": 28,
            "软座": 27,
            "硬座": 29,
            "无座": 26,
        }

        seat_data = {}
        for sname, idx in seat_price_indices.items():
            if idx < len(fields):
                val = fields[idx].strip()
                if val and val != "—" and val != "无" and val != "*":
                    seat_data[sname] = val

        trains.append({
            "车次": train_num,
            "出发站": dep_station,
            "到达站": arr_station,
            "出发": dep_time,
            "到达": arr_time,
            "历时": duration,
            "座位": seat_data,
        })

    if not trains:
        print(f"\n  ⚠ 无匹配车次（车次类型筛选太严格？）")
        return

    # ── 输出 ──
    print(f"\n{'='*100}")
    print(f"  {from_name} → {to_name}  |  {date}  |  共 {len(trains)} 趟车")
    if train_type:
        print(f"  筛选: {train_type} 字头")
    print(f"{'='*100}")

    for i, t in enumerate(trains, 1):
        line = (
            f"  {i:2d}. [{t['车次']:^6}]  "
            f"{t['出发']}→{t['到达']}  ({t['历时']})  "
            f"{t['出发站']}→{t['到达站']}"
        )
        print(line)

        # 座位信息
        if t['座位']:
            items = list(t['座位'].items())
            # 每行显示 4 个
            for j in range(0, len(items), 4):
                chunk = items[j:j+4]
                parts = []
                for sname, val in chunk:
                    parts.append(f"{sname}:{val}")
                print(f"    {'  '.join(parts)}")
        else:
            print("    无座位数据")
        print()

    print("=" * 100)

    # 简单统计
    g_count = sum(1 for t in trains if t['车次'].startswith('G'))
    d_count = sum(1 for t in trains if t['车次'].startswith('D'))
    c_count = sum(1 for t in trains if t['车次'].startswith('C'))
    other = len(trains) - g_count - d_count - c_count
    print(f"  G={g_count}  D={d_count}  C={c_count}  其他={other}")


def cmd_stations(keyword=None):
    """查找车站代码"""
    mapping = _fetch_station_map()
    if keyword:
        matches = [(k, v) for k, v in mapping.items() if keyword in k]
        print(f"\n🔍 搜索车站: '{keyword}' → {len(matches)} 个结果\n")
        for cn, code in sorted(matches)[:30]:
            print(f"  {cn:10s} → {code}")
    else:
        print(f"\n📋 车站总数: {len(mapping)}")
        print("用法: python3 12306_cli.py stations 北京")


# ── 入口 ──

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="12306 余票/票价查询（无需登录）")
    sub = parser.add_subparsers(dest="command")

    search_parser = sub.add_parser("search", help="查车次")
    search_parser.add_argument("from_station", help="出发站")
    search_parser.add_argument("to_station", help="到达站")
    search_parser.add_argument("date", help="日期 (YYYY-MM-DD)")
    search_parser.add_argument("--type", dest="train_type", help="车次类型: G/D/C/Z/T/K")
    search_parser.add_argument("--seats", action="store_true", help="只看二等/一等座票价")

    stations_parser = sub.add_parser("stations", help="查询车站代码")
    stations_parser.add_argument("keyword", nargs="?", help="搜索关键词")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args.from_station, args.to_station, args.date,
                   train_type=args.train_type, seats_only=args.seats)
    elif args.command == "stations":
        cmd_stations(args.keyword)
    else:
        parser.print_help()
