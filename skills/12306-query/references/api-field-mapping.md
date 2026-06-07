# 12306 余票查询 API 字段映射

> 接口: `https://kyfw.12306.cn/otn/leftTicket/queryZ`
> 参数: `leftTicketDTO.train_date`, `leftTicketDTO.from_station`, `leftTicketDTO.to_station`, `purpose_codes=ADULT`
> 无需登录，无需 Cookie

## 返回结构

```json
{
  "status": true,
  "data": {
    "result": ["field0|field1|...|field57", ...],
    "flag": "AdultsTicket",
    "map": { "BJP": "北京", ... }
  }
}
```

## 字段索引（共 58 个字段）

| 索引 | 含义 | 示例值 |
|------|------|--------|
| 0 | 唯一标识/密钥 | `gPqnrCnydFqBt0vugRhunHMtn8L8QZcIuCq2xAJmS1pXOZeP2a7ieuApRuJP` |
| 1 | 预订状态 | `预订` |
| 2 | train_no（票价API需要） | `240000G54700` |
| 3 | 车次号 | `G547` |
| 4 | 出发站代码 | `VNP` |
| 5 | 到达站代码 | `AOH` |
| 6 | 出发站代码（重复） | `VNP` |
| 7 | 到达站代码（重复） | `AOH` |
| 8 | 出发时间 | `06:18` |
| 9 | 到达时间 | `12:11` |
| 10 | 历时 | `05:53` |
| 11 | 是否可预订 | `Y` |
| 12 | 预留字段（长字符串） | — |
| 13 | 日期 | `20260610` |
| 14 | 预留 | — |
| 15 | 座位等级/代码 | `P3` |
| 16 | 预留 | — |
| 17 | 预留 | — |
| 18 | 预留 | — |
| 19 | 预留 | `0` |
| 26 | 无座 | `无`/`有`/数字 |
| 30 | 二等座 | `有`/`无`/数字 |
| 31 | 一等座 | `有`/`无`/数字 |
| 32 | 商务座 | `有`/`无`/数字(如`3`) |
| 34 | 编码票价串 | `90M0O0W0` |
| 35 | 编码串 | — |
| 36 | 预留 | — |
| 37 | 预留 | — |
| 39 | 编码票价串（长） | `9231500003M100500021O059800021O059803000` |
| 45 | 预留 | — |
| 46 | 车厢信息 | `5#1#Q0304#0#z#0#z#9MOW` |
| 47 | 编码串 | `O059800021` |
| 49 | 国家 | `CHN,CHN` |
| 54 | 编码票价串 | `90084M0079O0076W0076` |
| 55 | 数据更新时间 | `202605271245` |
| 56 | 是否有效 | `Y` |

## 座位类型 → 字段索引映射

| 座位类型 | 字段索引 | 说明 |
|---------|---------|------|
| 商务座 | 32 | 值: `有`/`无`/数字(余票数) |
| 特等座 | 33 | 部分列车该字段为空 |
| 一等座 | 31 | — |
| 二等座 | 30 | — |
| 高级软卧 | 21 | — |
| 软卧/动卧 | 23 | — |
| 硬卧 | 28 | — |
| 软座 | 27 | — |
| 硬座 | 29 | — |
| 无座 | 26 | — |

## 票价 API（需登录）

`https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice`
参数: `train_no`, `from_station`, `to_station`, `seat_types`, `train_date`

**注意**: 此 API 需要已登录 Cookie。未登录时返回登录页 HTML（`<title>铁路客户服务中心</title>`）。
当前 `12306_cli.py` 仅使用 `queryZ` 余票 API，不包含票价功能。

## 车站代码 API

`https://kyfw.12306.cn/otn/resources/js/framework/station_name.js`

格式: `var station_names = '@bjb|北京北|VAP|beijingbei|...'`
每段: `@代码|中文名|拼音缩写|拼音全称|...`
通过 `split("@")` 解析，`split("|")[1]` = 中文名，`split("|")[2]` = 3字母代码

## 脚本位置

`~/.hermes/scripts/12306_cli.py`
