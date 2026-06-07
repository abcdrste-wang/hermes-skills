---
name: bambu-lab-tips
description: "Bambu Lab 3D 打印机高级使用技巧 — 切片优化、材料设置、AMS 多色打印、校准流程、常见问题排查"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [3d-printing, bambu-lab, orca-slicer, fdm, calibration]
    related_skills: [3d-printing]
---

# Bambu Lab 3D 打印机高级技巧

本技能收录拓竹（Bambu Lab）3D 打印机（X1C/P1S/A1 Mini）的进阶使用技巧，重点覆盖 FDM 打印场景（PLA/PETG/TPU）。

## 软件选择

**推荐 Orca Slicer**（Bambu Studio 开源分支）：
- 内置完整的校准流程（温度塔、流量、Pressure Advance、最大流量）
- 更多高级功能：自适应层高、Arachne 壁生成器、围巾接缝
- 与 Bambu 打印机完全兼容（直接发送打印）

## 核心校准流程（Orca Slicer 内置）

在打印精细模型前，按顺序校准：

1. **温度塔** — 确定该卷料的最佳打印温度
2. **流量校准** — Pass 1 粗略 + Pass 2 精确
3. **Pressure Advance (PA)** — 最影响画质的单项，线形法
4. **最大流量测试** — 找到欠挤出临界点
5. **回抽测试** — 起始 0.8mm（Bambu 直驱），通常 0.6-1.2mm

### 常见材料的 PA 参考值
| 材料 | PA值 |
|------|------|
| PLA | 0.020 - 0.040 |
| PETG | 0.030 - 0.055 |
| TPU 95A | 0.080 - 0.120 |

### 常见材料的最大流量（0.4mm 喷嘴）
| 材料 | mm³/s |
|------|-------|
| PLA | ~21 |
| PETG | ~14 |
| TPU | ~4 |
| PLA (HF 喷嘴) | ~32 |

## 材料设置

### PLA
- 喷嘴：210-230°C
- 热床：55-65°C（首层65°C，后续55°C）
- 风扇：第3层后 100%
- **PLA Matte** — 表面质感好，隐藏层纹，适合展示件

### PETG ⚠️
- 喷嘴：240-260°C
- 热床：70-80°C
- 风扇：30-50%（过高 → 层间变脆）
- **流速降到 0.93-0.96** — 这是解决 PETG 大部分问题的关键
- **必须烘干**（尤其潮湿环境）

### TPU ⚠️
- 喷嘴：220-240°C
- 热床：40-50°C
- 速度：20-40 mm/s（极慢）
- 回抽：减少，否则堵头
- 风扇：0-20%
- **绝对不要进 AMS** — TPU 太软会卡住 AMS 齿轮
- 用外部料架（external spool holder）

## AMS 多色打印技巧

### 减少换料废料（可省 50-70%）
1. **降低 flush volume**：默认 300mm³ → 150-200mm³（简单换色）
2. **Flush into object**：废料打到支撑或打印件内部
3. **Flush into support**：利用支撑结构吸收废料
4. **颜色排序**：最常用颜色放 Slot 1（路径最短 → 最少废料）

### AMS 注意事项
- TPU ❌ — 不进 AMS
- PETG-CF ❌ — 除非是 Bambu 官方 PETG-CF（硬化路径）
- 干燥剂：AMS 有专门仓位，保持湿度 <20%
- 四色印刷技巧：prime tower purge volume 最低设 20mm³

## 常见问题排查速查表

| 问题 | 大概率解决方案 |
|------|--------------|
| 首层不粘 | 热水+洗洁精洗板（光酒精不够），首层速度降至 30mm/s |
| 拉丝 | 降温 5°C，回抽加至 1.2mm，开"Avoid crossing walls" |
| PETG 层间黏不牢 | 风扇降至 20%，升温 5°C |
| 欠挤出 | 流量 +2-3%，或检查部分堵头 |
| 过挤出（PETG） | 流速比 0.93-0.95 |
| 表面有疙瘩 | 开"Avoid wiping while retracted"，降低 coasting |
| AMS 送料失败 | 清理 AMS 进料 PTFE 管，减少线材阻力 |
| 层偏移 | 紧 X/Y 皮带，检查卡死，降低加速度 |
| 堵头 | 冷拉（冷拔）：加热到 230°C，冷却到 90°C，拉出 |
| 翘边 | 加 brim，关舱门（ABS/ASA），PETG 可用 draft shield |

## Hotend 与平台

### 喷嘴
- **HF (High Flow) 喷嘴**：PLA 最大流量从 21→32 mm³/s，需重调 PA
- 硬化钢喷嘴：打印碳纤/玻纤增强材料必需

### 平台选择
| 板型 | 适用材料 |
|------|---------|
| Cool Plate（光面）| PLA, PETG |
| Engineering Plate | ABS, PA |
| Textured PEI | TPU, PETG |
| High Temp Plate | PA, PET-CF |

### 其他硬件技巧
- 箱内风扇：PLA 打印时关掉或开顶盖（热累积会让 PLA 变软）
- 5015 吹风扇升级（X1/P1S 第三方）：改善悬垂质量
- Bambu Handy App：关掉 Timelapse → 减少层间移动 → 更快的打印
- 输入整形 (Input Shaper)：固件自动校准；手动触发 `G-Code: M1001` 重新测量

## 打印猫类关节模型特别建议

- **尾巴用 TPU** — 可弯曲，打印后用外部料架
- **身体/头/腿用 PLA Matte** — 表面光滑，隐藏层纹
- **关节间隙 0.4mm** 已足够（标准喷嘴宽度）
- 打印前用 **Blender 3D Print Toolbox** 或 **trimesh** 检查水密性
- 不需要支撑（设计时确保无悬垂）

## 有用的 G-code 宏

```gcode
; 强制输入整形重新校准
M1001

; 腔室风扇控制（关闭）
M106 P2 S0

; LED 灯
M150 R255 U0 B0 P255   ; 红灯
M150 R0 U255 B0 P255    ; 绿灯

; 换料时清除废料
M620
```

## 关联资源

- **3d-printing** skill — 程序化生成 STL 模型的基础技能
- **Orca Slicer 官方 Wiki**: https://github.com/SoftFever/OrcaSlicer/wiki
- **r/BambuLab** — 中文拓竹社区活跃
