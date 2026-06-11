# Hermes 3D 建模全技能清单

> 创建日期：2026-06-11
> 来源：`3d-printing` SKILL.md（2652行） + 21 个参考文件 + 实测经验
> 用途：快速定位"遇到这个情况该查哪个文件"

---

## 一、建模前决策 — 选哪个范式

| 场景 | 范式 | 工具链 | 参考文件 |
|------|------|--------|---------|
| 枪械/车辆/机械 | 侧面轮廓挤出 | Blender bmesh | `weapon-side-profile-extrusion.md` |
| 能量剑/管状体/有立体感的武器 | 椭圆截面堆叠 (Lofting) | Blender bmesh | `elliptical-lofting-weapon.md` |
| 卡通角色（动物/人物/玩具） | 分部件建模 + 布尔合并 | Blender bmesh | `cartoon-character-modeling.md` |
| 手机壳/平面功能性零件 | numpy-stl 几何组合 | Python numpy-stl | `numpy-stl-phone-case.md` |
| 精确参数化零件（卡扣/齿轮/连接件） | CadQuery 设计 → Blender 美化 | CadQuery + Blender | SKILL.md §4 CadQuery 集成 |

### 决策流程图

```
用户说了一个模型
  ↓
参考图——我用 Qwen3-VL-Plus 分析总体类型
  ↓
什么类型的模型？
├── 枪/武器/能量剑 → 看参考图是侧视轮廓清楚还是枪管截面清楚
│   ├── 侧视轮廓非常独特 → 侧面轮廓挤出法
│   └── 管状物/能量刃 → 椭圆截面堆叠法
├── 卡通角色 → 分部件建模法（25+ 零件清单）
├── 功能性零件/外壳 → numpy-stl / CadQuery
└── 不确定 → 先搜索参考图再做判断
```

---

## 二、流程节点快速定位

### 1. 拿到参考图后
- **参考图方向判断模糊？** → `references/ai-generated-reference-ambiguity.md`（AI 生成参考图的方向模糊是正常的，打印时可旋转）
- **用 AI 分析参考图？** → 用 Qwen3-VL-Plus（不是 GLM-4v！），详见 `references/qwen3-vl-plus-vision-for-3d.md`
- **GLM-4v 报"不存在"某部件？** → 不可信！GLM 在几何参照场景有明确幻觉，参考你的肉眼推理

### 2. 建模过程中
- **侧面轮廓点怎么提取？** → `weapon-side-profile-extrusion.md` §1 轮廓点提取（30-50 个点起步）
- **椭圆截面怎么定义？** → `elliptical-lofting-weapon.md` §参设计模式（piecewise functions）
- **Blender 中 SUBSURF modifier apply 不生效？** → `blender-modifier-headless-pitfall.md`（headless 下所有 modifier_apply 静默失败）
- **怎么绕过 modifier 做细分？** → `blender-headless-bmesh-subdivide.md`（用 bmesh.subdivide_edges）
- **怎么做镜像对称？** → 用 `bmesh_symmetrize_mirror()` 函数（SKILL.md § BMesh）
- **Blender 5.x API 细节记不清？** → `blender-5.1-api.md`（STL 导出、渲染引擎枚举等）

### 3. 已有 STL 文件要修改
- **给已有 STL 加零件（枪管/瞄准镜/握把等）** → `stl-editing-workflow-case-study.md`
- **从已获批模型轮廓重建干净几何** → `approved-model-contour-rebuild.md`
- **从参考图提取轮廓 + 高斯平滑 + 挤出** → `contour-extraction-smoothing-pipeline.md`
- **把大 STL 拆分为多部件打印** → `weapon-blender-modeling.md` §Blender 常用 Python 工具

### 4. 渲染/预览
- **默认预览方案** → `scripts/stl_2d_preview.py`（PIL 面法线着色 + 三点光源）
- **用户说"全黑"** → 先查 STL 顶点范围（检查脚本在 `debug-render-all-black.md` §第 0 步）
- **EEVEE 渲染全黑诊断** → `debug-render-all-black.md`（完整 3 步修复策略）
- **长条物体侧视构图** → SKILL.md §长条/细长物体的 ORTHO 侧视图构图策略（ORTHO scale 自动公式）
- **M4 上的 EEVEE 不可用** → SKILL.md §EEVEE 渲染优化（RR 版）— 已实测 Blender 5.1.2 headless 纯黑帧
- **Cura 作为渲染替代方案** → `cura-as-render-alternative.md`

### 5. 水密性修复
- **快速检测水密+边界边** → SKILL.md §诊断脚本（python3 -c 一行命令）
- **边界边 < 50** → trimesh `fill_holes()` 可能自动修复
- **边界边 50-500** → 尝试 Blender 自动补洞 + remove_doubles
- **边界边 > 500** → Blender edit-mode 手动修复（repair_watertight_edit_mode 函数）
- **trimesh vs Blender 水密判断差异** → SKILL.md §已验证的差异表（trimesh 报告的额外非流形边不影响切片）

### 6. 质量把关（发用户前必须做）
- **自检清单** → SKILL.md §Verification（三角面数、STL 顶点范围、文件大小、像素亮度）
- **用户任务指令协议** → `user-task-brief-protocol.md`（用户给的编号清单是精确指令，不能自己加额外要求）
- **FFAR1 建模全过程复盘** → `ffar1-modeling-case-study.md`（8 版迭代的完整教训）
- **关节设计** → SKILL.md §关节设计方法论（球关节/铰链/拆分打印策略）

---

## 三、要点速查

### M4 Mac Mini 的硬约束
| 问题 | 现象 | 替代方案 |
|------|------|---------|
| EEVEE headless 渲染 | 纯黑帧或灰度缺陷（Blender 5.1.2） | `stl_2d_preview.py` PIL 线框预览 |
| Modifier apply 静默失败 | SUBSURF/MIRROR/BOOLEAN 不生效 | bmesh 直接操作顶点/边/面 |
| ORTHO 侧视细长物体 | 画面 86% 是背景 | 用 PERSP 相机，lens ≥ 85mm |
| IM 图片压缩 | 大 PNG 变全黑 | JPEG 800×600 ≤ 200KB |

### 参考图分析 — AI 视觉模型选择
| 模型 | 3D 几何推理 | 可靠性 | 成本 |
|------|------------|--------|------|
| Qwen3-VL-Plus (阿里百炼) | 有"空间感知"能力 | ✅ 首选 | ¥2.5-5/M tokens |
| GLM-4v (智谱) | 有明确幻觉（误报/漏报部件） | ❌ 不可靠 | 免费 |
| **强规则** | GLM 报告"不存在"的部件，肉眼推理说在 → 信肉眼 | | |

### 建议三角面数
| 模型类型 | 目标面数 | 备注 |
|---------|---------|------|
| 武器/能量剑 | 3000-5000 | FFAR1 v8 = 2080 顶点，约 ~4000 面 |
| 卡通角色 | 5000-8000 | 25+ 零件，不可用 Decimate（会破坏细节） |
| 手机壳 | 500-2000 | 不需要高面数 |
| 低于 376 面 | ❌ 不可接受 | 典型 box 组合，用户说"看不出样子" |
| 超过 1 万面 | STL > 500KB | IM 传输不便，需压缩 |

---

## 四、文件索引

```
creative/3d-printing/
├── SKILL.md                         ← 核心手册（2652行）：所有基础知识+代码模板+渲染协议+验证清单
│
├── references/                      ← 参考文件（22个）
│   ├── weapon-side-profile-extrusion.md             侧面轮廓挤出法完整流程
│   ├── elliptical-lofting-weapon.md                 椭圆截面堆叠法
│   ├── cartoon-character-modeling.md                卡通角色分部建模法
│   ├── ffar1-modeling-case-study.md                 FFAR1 8版迭代复盘
│   ├── approved-model-contour-rebuild.md            已获批模型的轮廓重建
│   ├── contour-extraction-smoothing-pipeline.md     轮廓提取+高斯平滑流水线
│   ├── stl-editing-workflow-case-study.md           STL 编辑/加件/切割
│   ├── weapon-blender-modeling.md                   Blender 武器建模+5.x 导出修复
│   ├── numpy-stl-phone-case.md                      numpy-stl 手机壳建模
│   ├── blender-5.1-api.md                           Blender 5.x API 差异
│   ├── blender-5x-modifier-names.md                 5.x 修改器名称变化
│   ├── blender-modifier-headless-pitfall.md          headless modifier 静默失败
│   ├── blender-headless-bmesh-subdivide.md           bmesh 替代 SUBSURF
│   ├── debug-render-all-black.md                    全黑渲染诊断 3 步法
│   ├── cura-as-render-alternative.md                Cura 切片预览替代渲染（M4无独显）
│   ├── ai-generated-reference-ambiguity.md           AI 生成参考图方向模糊
│   ├── qwen3-vl-plus-vision-for-3d.md               Qwen3-VL-Plus 视觉能力
│   ├── user-task-brief-protocol.md                  用户编号指令处理规范
│   ├── game-skin-research-workflow.md               游戏皮肤参考研究流程
│   ├── one-piece-boolean-union.md                   一体打印布尔合并
│   └── articulated-cat-example.md                   铰接关节示例
│
├── scripts/
│   └── stl_2d_preview.py             ← 默认预览脚本（PIL 面法线着色+三点光源）
│
└── hermes-3d-modeling-expert-playbook.md   ← 本文件（全技能清单导航）
```

---

## 五、快速启动

```
新模型任务 →
1. 加载 3d-printing skill: skill_view(name='3d-printing')
2. 参考图分析: Qwen3-VL-Plus（确认模型类型、关键部件）
3. 选范式：侧面轮廓挤出 / 椭圆截面堆叠 / 分部件建模 / numpy-stl / CadQuery
4. 查对应参考文件
5. 建模脚本 → Blender headless 运行
6. 验证：三角面数 ≥ 3000、STL 顶点各轴 > 2mm、质心 Z>0
7. 预览：stl_2d_preview.py（默认）/ Cura 切片预览（实体体积）/ EEVEE（用户明确要彩色时）
8. 自检：对照参考图，逐件对比
9. 发用户
```
