---
name: 3d-printing
description: "Generate FDM-ready 3D printable STL models — one-piece boolean-UNION character models (Blender), multi-part articulated designs (numpy-stl), phone cases, and custom parts. Covers the full pipeline: modeling → boolean merge → flat base plate → STL export → render preview → bed adhesion verification."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [3d-printing, stl, fdm, cad, generative-design, articulated, multi-part, numpy-stl, blender, boolean-union, one-piece, character-modeling, phone-case]
    related_skills: [sketch, spike, python-3d-tools, bambu-lab-tips]
---

# 3D Printing — 实物还原建模专家（正向设计+逆向复刻）

> **定位**：负责所有实物还原建模任务，最终产出合规、可直接切片打印的STL，兼顾精度、拓扑和打印可行性。
> 
> 本技能涵盖正向设计（从零建模）和逆向复刻（从实物/参考图还原），输出FDM/光固化可用的STL文件。
> 
> 来源：用户系统化知识沉淀（2026-06-08）

## 核心能力体系

### 1. 通用三维基础
- 三维空间逻辑、坐标系、点/线/面/体拓扑原理
- 理解流形网格(manifold)、法线方向、拓扑连续（STL硬性要求）
- 尺寸标注、公差、实体尺寸还原（对标实物长宽高、弧度、卡扣、凹槽）
- 单位规范：默认毫米制(mm)，熟练切换 mm/inch

### 2. 三大建模流派

**（A）参数化实体建模** — 硬件、标准件、结构件首选
- 草图约束、特征建模：拉伸、旋转、倒角、圆角、孔、阵列、抽壳、布尔运算
- 装配逻辑：零件配合、卡扣、螺纹、榫卯、过盈配合
- 特征修复：处理破面、重叠面、无效布尔

**（B）曲面/多边形建模** — 异形、曲面、有机件、复杂外观
- 曲面重构：弧面、流线型、不规则轮廓拟合
- 多边形网格编辑：面合并、删废面、修复非流形、减面/拓扑优化
- 逆向造型：从实物轮廓/点云反向重建曲面

**（C）椭圆截面堆叠（Lofting）** — 枪械、武器、异形管状件首选
- 原理：在不同高度（沿Y/Z轴）定义不同大小和形状的椭圆截面，每个截面由椭圆方程控制
- 优势：比侧面挤压（薄片）产生真实3D体积，比box composite（方块堆叠）更平滑
- ⚠️ 核心教训：侧面轮廓挤压（side-contour extrusion）无论顶点数多少，做出来都是纸片/薄片效果。FFAR1案例中v3-v5尝试了1465个轮廓点+挤出的方法，260~640面，视觉上"像纸片"。椭圆截面堆叠是替代方案，它能产生真实3D立体感。
- 适用：需要立体感但不是纯圆柱/圆锥的异形管状物体（枪身、剑柄、能量武器）
- 不适合：平面特征为主的物体（建筑、机械箱体）

### 3. 逆向还原核心
- 实物测绘：卡尺测量、轮廓描点、截面提取
- 点云/扫描数据处理：降噪、精简、对齐、截面提取
- 逆向重构：点云→轮廓线→曲面/实体
- 对称重构：利用对称性减半工作量

### 4. STL 专项合规（对接3D打印）
- STL标准：三角面片、封闭壳体、无破洞、无重叠面、法线统一朝外
- 模型检查：识别修复破面、悬空面、交叉面、零面积三角面、内壁穿透
- 壁厚设计：FDM ≥1.2mm，树脂 ≥0.6mm
- 支撑预判：悬空/悬挑结构优化或预留支撑位
- 模型轻量化：合理减面不损外形

### 5. 切片&打印适配
- 区分FDM/光固化两种工艺，针对性优化模型
- 模型分件、卡扣拼接设计（过打印机尺寸时）
- 拔模角度、公差补偿（0.1-0.2mm装配间隙）

### 6. 顶级进阶能力
- 拓扑优化：减重、加强筋布局
- 误差修正：±0.1mm 精度控制
- 多格式互转：STEP/IGS/OBJ/STL
- 批量处理：批量修复/导出/减面
- 故障排错：切片报错、断层、翘边、坍塌

## 🧠 AI视觉模型能力表（3D建模用）

当`vision_analyze`用于审查3D渲染图和参考图时，不同模型有显著差异：

| 模型 | 适用场景 | 可靠性 | 已知问题 |
|------|---------|--------|---------|
| **GLM-4v-Flash（智谱）** | 图片概览、分类判断 | ★★☆ | 三维几何参照幻觉严重——报告"没有枪口制退器"但图中明显可见；报告"看不到弹匣"但侧面明显可见。会同时编造「存在」和「不存在」的部件 |
| **Qwen3-VL-Plus（阿里百炼）** | 多模态视觉理解、空间感知 | ★★★☆ | 需DashScope API Key（sk-sp-xxx格式，通过DASHSCOPE_API_KEY或ALIBABA_API_KEY环境变量配置）。效果优于GLM-4v但非免费。不可用于精确尺寸测定<br><br>**⚠️ ACL/GPCR 幻觉**: 当渲染图中有棱角/网状结构时，Qwen3-VL-Plus 可能将其误认为生物分子结构（蛋白质/GPCR）。FFAR1 武器渲染曾被误判为 "GPCR 蛋白结构"——因为 FFAR1 本身是一个真实存在的游离脂肪酸受体蛋白，模型将视觉上与已知文字"FFAR1"关联。评估成品渲染时必须同时提供原始参考图。 |
| **DeepSeek文本模型** | ❌ 无视觉能力 | — | 不能用来看图 |

**关键经验：** 所有AI视觉模型在推断3D几何时都可能产生幻觉。**绝对不可以以vision_analyze说的"这个部件不存在"作为不建模的依据。** 部件存不存在要以参考图为准（B站截图、官方概念图），AI判断只能做概览。

视觉模型配置位于 `auxiliary.vision` 段，对应的API Key在 `.env` 中设置。**关键修复：国内DashScope Key必须修改 `auth.py` 中硬编码的国际版Base URL** — 详情见 `hermes-agent` 技能的 `references/alibaba-dashscope-domestic-key-fix.md`。

```yaml
# config.yaml — 阿里百炼 Qwen3-VL-Plus 作为视觉模型
auxiliary:
  vision:
    provider: alibaba
    model: qwen3-vl-plus
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
```
`.env` 中设置 `DASHSCOPE_API_KEY=sk-sp-xxx...`（阿里百炼专属格式）。

```yaml
# config.yaml — 智谱 GLM-4v-Flash 作为视觉模型（免费备选）
auxiliary:
  vision:
    provider: zai
    model: glm-4v-flash
    base_url: https://open.bigmodel.cn/api/paas/v4/
```
`.env` 中设置 `GLM_API_KEY=xxx...`（bigmodel.cn 标准格式）。

**切换注意：** 主模型（`model.provider`）必须保持 `deepseek`，不能改成 `alibaba` 或 `zai`。视觉模型独立于主模型配置，只影响 `vision_analyze()` 的调用。

## 安装状态（2026-06-08 当前）

| 工具 | 状态 | 安装命令 | 说明 |
|------|------|---------|------|
| **trimesh 4.12.2** | ✅ 已装 | `pip3 install trimesh networkx` | 自动化质检：水密性、体积、组件分析、STL repair、几何体生成 |
| **Blender 5.1.2** | ✅ 已装 | `/Applications/Blender.app` | 全套建模+渲染 |
| **numpy-stl 3.2.0** | ✅ 已装 | `pip3 install numpy-stl` | 纯 Python 几何体组合 |
| **networkx 3.2.1** | ✅ 已装 | 随 trimesh 自动安装 | 图分析依赖 |
| **UltiMaker Cura 5.13.0** | ✅ 已装 | `brew install --cask ultimaker-cura` | 切片软件，内置 STL 修复（补洞、水密检查、可打印性验证） + 可作临时实体预览替代渲染 |
| **CadQuery 2.5.2** | ❌ 未装 | GFW 下 `pip3 install cadquery` 超时（casadi 42MB + OCP C++绑定） | 参数化 CAD 零件卡扣/齿轮/连接件 |
| **f3d** | ❌ 未装 | GFW 下 `brew install f3d` 超时 | 快速 STL 预览（0.5s vs Blender 3-5s） |
| **scipy** | ❌ 未装 | GFW 下超时 | trimesh 的 body_count 检测依赖 |
| **openscad** | ❌ 未装 | `brew install openscad` | 参数化规则件 |
| **Meshmixer** | ❌ 已停维护 | 已从官网/brew下架，无安装方式 | ❌ 不再可用。替代：Bambu Studio/Cura 内置修复 + trimesh Python 修复 |

> **当前工作流**: trimesh 做所有自动化质检和修复，Blender 做精细建模+渲染，numpy-stl 做快速几何体生成。缺少 CadQuery 时，参数化功能零件用 Blender bmesh 替代。缺少 f3d 时，Blender EEVEE 渲染替代预览。
>
> **一键安装脚本**: `bash ~/.hermes/scripts/install_3d_tools.sh`（走代理+国内镜像，可能需要多次尝试）

## 软件工具栈

### 主力建模（二选一主用）

**方案A — 工业参数化路线**（机械/标准件/结构实物首选）
- **Fusion 360**（首推）：参数化+自由曲面+逆向一体，原生STL导入导出
- 备选：SolidWorks（精密机械装配）

**方案B — 多边形/曲面路线**（异形/艺术品/手办/曲面实物首选）
- **Blender**（首推）：免费开源，多边形网格编辑、曲面重塑、拓扑重构
- 备选：Rhino（工业曲面王者，NURBS→STL精度极高）

### 逆向扫描&点云处理
- **MeshLab**（免费必备）：降噪、精简、对齐、截面提取
- **CloudCompare**（免费）：高精度点云对齐、误差比对
- 商用：Geomagic Design X（工业级点云→实体全自动逆向）

### STL 修复/校验（打印零报错核心）
- **Meshmixer** ❌ 已停维护（2026起不可安装）—— 替代方案见下方
- **Bambu Studio / Orca Slicer** ✅ 内置STL修复、壁厚检测、支撑生成（免费跨平台）—— Meshmixer 最佳替代
- **UltiMaker Cura** ✅ 内置STL修复、切面检测
- **Netfabb**：工业级STL检查、拓扑修复（需Windows/企业许可证）

### 切片软件（验证STL可用性）
- **Cura**：FDM通用
- Chitubox / Lychee Slicer：光固化

### 硬件外设
- 数显卡尺（0.01mm精度）
- 三维扫描仪：桌面级→手持式→工业级
- 轮廓规、高度规、角度尺

### 插件
- Blender: 3D Print Toolbox, Remesh
- Fusion 360: 扫描逆向插件
- MeshLab: 批量修模脚本

> **快速导航**：如果你不确定当前在哪个流程节点、该查哪个参考文件，先打开 `references/hermes-3d-modeling-expert-playbook.md` —— 那是整个技能体系的"导航地图"，5 分钟定位到对应的文件和流程步骤。

## 标准工作流

### 流程1：手动测绘复刻（无扫描仪）
```
实物测量 → 草图绘制 → 参数化实体/曲面建模 → 检查壁厚/结构 → 导出STL → Meshmixer修复 → Cura校验 → 交付打印
```

### 流程2：三维扫描逆向复刻（高精度）
```
实物扫描 → 点云→CloudCompare/MeshLab降噪/对齐 → 导入Fusion/Blender重构 → 结构优化(壁厚/支撑/分件) → STL导出+修复 → 切片验证 → 交付
```

## 推荐软件组合

| 方案 | 建模 | 逆向/修模 | 切片 | 场景 |
|------|------|-----------|------|------|
| **全能免费栈** | Fusion 360 + Blender | MeshLab + Meshmixer | Cura | 个人/小型场景，覆盖90% |
| **工业高精度** | SolidWorks / Rhino | Geomagic + CloudCompare | Netfabb | 精密零件、商用 |
| **艺术/手办** | Blender + Rhino | MeshLab | Meshmixer + Lychee | 文创、雕塑、异形件 |

## 🔄 STL 文件接收协议 — 用户丢来一个 .stl/3mf 文件时

**场景**: 用户通过聊天直接发给你一个 STL 文件（可能包含关键词 `TEMI`/`single_color`/`stl`），但没有说明要做什么。

**规则：不要直接跑完整流水线。** 先问清楚需求。用户可能只是：
- 想你看一眼是什么模型（无需处理）
- 想让你优化/减面/缩放
- 想让你改模型（加特征、修破面、改尺寸）
- 只是发文件作为参考，没要求处理

**推荐的确认方式（多选模式）：**
> 你发了一个 STL 文件（xx万面，xxMB，约 xxxmm 尺寸）。你想怎么处理？
> 1️⃣ 就看一眼是什么模型
> 2️⃣ 减面优化+修复
> 3️⃣ 调整尺寸/缩放
> 4️⃣ 改模型结构
> 
> 或者直接说用途

只有用户明确表态后再开流水线。如果用户只回了一个符号（如 `？`），说明你做过头了——老实承认，不用解释。

## 🏆 Expert Position: Own the full pipeline

**Hard rule: When the user gives you a 3D modeling task, you are THE expert. Do NOT ask the user which tools are needed, whether a tool is "enough", or what approach to take.** The user has made this expectation explicit: "你是一个3D建模专家，你要自己找工具完成".

This means:
- **You decide** what tools are needed (Blender + Cura + trimesh = current stack)
- **You decide** when a tool is "enough" (Cura's auto-repair suffices for minor non-manifold issues)
- **You decide** the workflow sequence (analyze → fix → validate → preview)
- **You report** status and results, not ask permission for tool choices
- If you need a new tool, research it yourself, install it yourself, then use it

**例外情况**：只有当工具需要付费、需要用户执行GUI操作（如扫码登录）、或涉及用户硬件购买决策时才问用户。纯工具/工作流选择不关用户的事。

**Fallback protocol** (when your current toolset genuinely cannot solve the problem):
1. Research alternative approaches via web_search immediately (do not iterate failed approach)
2. If the fix needs a new tool, install it yourself and test it
3. If the fix is fundamentally beyond software (physical hardware needed), state the limitation factually and offer a workaround

## 🛠️ STL 编辑工作流 — 在已有的 STL 上做修改（加/减特征）

**场景**: 用户发来一个现有的 STL 文件（如 Bambu AI 生成的白模、下载的模型、别人发的文件），要求在上面做修改：加洞、切掉一部分、加新特征、合并另一模型等。

**这是与「从零建模」截然不同的工作流。** 不要把编辑任务当作建模任务从零开始。

### Phase 0: 检查任务性质

用户说的"改模型"可能包含多种任务类型，必须先确认：

| 任务类型 | 用户会说 | 工作流 |
|---------|---------|-------|
| **减法**（切掉/删除部件） | "三枪口改一个" "削高留矮" "去掉这个尖尖" | Bisect/顶点删除 + 网格填充 |
| **加法**（加新零件） | "加个碟片" "加耳朵" "加个底座" | 新建 miniface + extrude 或 add primitive 再合并 |
| **切割保留**（保留另一部分） | "切掉枪口，保留主体" "只留前一半" | Bisect clear_inner/clear_outer |
| **缩放/修改尺寸** | "放大20%" "壁厚改到1.2mm" | Scale 变换 + shell/reduce |
| **合并**（两个文件合一） | "把枪管和枪身合并" | 分别导入后 join |

### Phase 1: 分析原模型

**编辑前，必须先了解模型的尺寸、方向、关键位置。** 这步做错了后面全白费。

```bash
python3 -c "
import numpy as np
for fname in ['your_model.stl']:
    with open(fname, 'rb') as f:
        data = f.read()
    num_tris = int.from_bytes(data[80:84], 'little')
    verts = []
    for i in range(num_tris):
        offset = 84 + i * 50
        for j in range(3):
            v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
            verts.append(v)
    verts = np.array(verts)
    print(f'{fname}: {num_tris} tris')
    print(f'  X: {verts[:,0].min():.1f} ~ {verts[:,0].max():.1f}  (range: {verts[:,0].ptp():.1f})')
    print(f'  Y: {verts[:,1].min():.1f} ~ {verts[:,1].max():.1f}  (range: {verts[:,1].ptp():.1f})')
    print(f'  Z: {verts[:,2].min():.1f} ~ {verts[:,2].max():.1f}  (range: {verts[:,2].ptp():.1f})')
    print(f'  Volume: {verts[:,:].ptp(axis=0).prod():.0f} mm³ (approx bbox)')
    print(f'  Centroid: ({verts[:,0].mean():.1f}, {verts[:,1].mean():.1f}, {verts[:,2].mean():.1f})')
"
```

### Phase 2: 编辑策略

**核心原则: 使用 bmesh 直接操作，不要用 modifier（headless 下 modifier_apply 静默失败）。**

因 Blender headless 模式下 modifier 的 apply 操作会静默失败（BOOLEAN/MIRROR/SUBSURF/BEVEL 全部受影响），编辑已有 STL 时必须使用 bmesh 直接操作顶点/边/面。

#### 减法模式（切掉/删除部分顶点区域）

```python
import bpy, bmesh, math

# 1. 导入 STL
bpy.ops.wm.stl_import(filepath='input.stl')
obj = bpy.context.object
me = obj.data

# 2. 进入 bmesh 编辑模式
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(me)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# 3. 选择目标区域 (示例: 删除 Y>49 的所有顶点 — 枪口端)
target_verts = [v for v in bm.verts if v.co.y > 49.0]
bmesh.ops.delete(bm, geom=target_verts, context='VERTS')

# 4. 封口 — grid fill 自动三角剖分开口
# 先找到开口边（只属于一个面的边）
open_edges = [e for e in bm.edges if len(e.link_faces) == 1]
# 用 fill 封成大面，再三角剖分
bmesh.ops.grid_fill(bm, edges=open_edges, mat_nr=0, use_smooth=True, use_interp_simple=True)
# 或者用 hole_fill（更简单但可能质量差）
# bmesh.ops.holes_fill(bm, edges=open_edges)

# 5. 写入
bmesh.update_edit_mesh(me)
bpy.ops.object.mode_set(mode='OBJECT')
```

#### 加法模式（添加新零件到已有模型）

```python
# 在已有 STL 上加新零件

# 1. 创建新零件作为独立 mesh
new_mesh = bpy.data.meshes.new("NewPart")
bm2 = bmesh.new()
verts = [
    bm2.verts.new((x1, y1, z1)),
    bm2.verts.new((x2, y2, z2)),
    # ...
]
bm2.faces.new(verts)  # 按需要构建面
bm2.to_mesh(new_mesh)
bm2.free()

new_obj = bpy.data.objects.new("NewPart", new_mesh)
bpy.context.collection.objects.link(new_obj)

# 2. 用 join 合并到主模型（不要用布尔 UNION — headless 下 BOOLEAN modifier apply 静默失败）
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
new_obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.join()  # 简单合并，允许内部重叠面
# ⚠️ 这会产生内部面（不是水密模型），但对 3D 打印通常可接受
# 打印前在 Bambu Studio/Cura 中会自动处理重叠区域

# 3. 或者用 trimesh 做布尔 UNION（Python 非 Blender 方式）
# pip3 install trimesh
import trimesh
import numpy as np

main = trimesh.load('input.stl')
# 创建新零件 mesh
new_part = trimesh.Trimesh(vertices=..., faces=...)
# 布尔 UNION — 合并为一个水密网格
result = trimesh.boolean.union([main, new_part])
result.export('output.stl')
```

#### 先减法再加法（完整编辑模式）

```python
# FFAR1 武器模型编辑实例 (500K faces):
# 任务: 1)切掉三枪口→改单枪口 2)削瞄准镜高尖 3)加碟片

# Step A: 导入 + 分析
bpy.ops.wm.stl_import(filepath='bambu_model.stl')
obj = bpy.context.object

# Step B: 删除枪口端区域
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)
bm.verts.ensure_lookup_table()
# 选中 Y>49 的所有顶点
del_verts = [v for v in bm.verts if v.co.y > 49.0]
print(f"Deleting {len(del_verts)} vertices on muzzle end")
bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
# 封口
bm.edges.ensure_lookup_table()
open_edges = [e for e in bm.edges if len(e.link_faces) == 1]
bmesh.ops.grid_fill(bm, edges=open_edges, mat_nr=0, use_smooth=True)
bmesh.update_edit_mesh(obj.data)
bpy.ops.object.mode_set(mode='OBJECT')

# Step C: 添加新零件（枪口帽 — 半圆球）
bpy.ops.mesh.primitive_uv_sphere_add(radius=8.5, location=(0, 50, 4))
cap = bpy.context.object
# 做半球：在编辑模式删除上半部分
bpy.ops.object.mode_set(mode='EDIT')
# ... 选择删除部分顶点

# Step D: 削瞄准镜 — 删除尖顶区域
# 选中 Z>15 的顶点并删除

# Step E: 加碟片 — 创建圆柱或圆环并 join
bpy.ops.mesh.primitive_cylinder_add(radius=3.5, depth=1, location=(6.5, 20, 4))

# Step F: 全部 join
bpy.ops.object.select_all(action='DESELECT')
main_obj.select_set(True)
for part in [cap, disc]:
    part.select_set(True)
bpy.context.view_layer.objects.active = main_obj
bpy.ops.object.join()

# Step G: 导出
bpy.ops.wm.stl_export(filepath='output.stl', export_selected_objects=True)
```

### Phase 3: 暴力验证 — 编辑后的 STL 面数/体积/位置检查

编辑操作后**必须**立刻做检查，这是最常见出问题的地方：

```python
# 检查编辑后 STL 的面数、体积、顶点范围是否合理
import numpy as np
fname = 'edited_model.stl'
with open(fname, 'rb') as f:
    data = f.read()
num_tris = int.from_bytes(data[80:84], 'little')
verts = []
for i in range(num_tris):
    offset = 84 + i * 50
    for j in range(3):
        v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
        verts.append(v)
verts = np.array(verts)
ranges = [verts[:,i].ptp() for i in range(3)]

# 诊断
problems = []
if num_tris < 50:
    problems.append(f"面数暴跌: {num_tris} — 模型几乎被删光了")
if ranges[2] < 1.0:
    problems.append(f"Z 方向仅 {ranges[2]:.1f}mm — 模型被压扁/平躺？")
if verts[:,2].mean() < -10:
    problems.append(f"质心在 Z={verts[:,2].mean():.1f} — 相机默认角度拍不到")

print(f"面数: {num_tris} {'✅' if num_tris > 1000 else '⚠️'}")
print(f"体积(bbox): {ranges[0]*ranges[1]*ranges[2]:.0f} mm³")
print(f"XYZ范围: {ranges[0]:.1f} x {ranges[1]:.1f} x {ranges[2]:.1f}")
if problems:
    for p in problems:
        print(f"❌ {p}")
else:
    print("✅ 基本检查通过")
```

### ⚠️ 编辑 STL 常见陷阱

| 陷阱 | 表现 | 修复 |
|------|------|------|
| Bisect 方向反了 | 切出来体积只剩 100mm³（原来 5000mm³）—— 主体被删了 | `clear_inner=True` 删除平面内侧的区域；`clear_outer=True` 删除外侧。先确认哪个方向是"枪口方向" |
| 删除顶点后网格破裂 | 面数正常但模型有洞/非流形 | 使用 `bmesh.ops.grid_fill()` 封口，不要手动捏面 |
| 零件添加后 stuck inside | 面数增加了但体积没变化 | 新零件完全在主模型内部（穿透但未超出边界）—— 需把新零件位置放在模型表面 |
| 原模型面数太大 | 50万面，Blender 操作很慢 | 对原模型用 `bmesh_subdivide_for_smoothness` 降面（多用在 trimesh 中做简化） |
| 用户用3点清单表达需求 | "三个主要问题：1. X 2. Y 3. Z" | 这是精确指令，不能自己加额外要求。用户说"中间不需要特效"就是不需要，不用自作主张 |

---

## Phase 0: 查工具+定方案（建模前必须执行）

### 📦 Render Preview 方案矩阵（按M4无独显环境）

用户通过飞书/Telegram看到渲染图。渲染不佳=你白做了。**这是用户反馈最频繁的瓶颈。**

### 渲染引擎选择

| 方案 | 速度 | 质量 | 适用场景 | 备注 |
|------|------|------|---------|------|
| **2D线框投影（stl_2d_preview.py）** | ⚡ <1s | ★★ | 形状/结构验证 | 首选，可靠，无GPU依赖 |
| **Cura切片预览截图** | ⚡ 2s | ★★★ | 形状/打印可行性验证 | 🆕 2026-06发现的新方案：Cura带模型修复功能，切片后可看实体轮廓 |
| **Blender EEVEE headless** | 🐢 3-5s | ★ | ❌ M4无独显下全灰不可用 | 已证明不可靠，跳过 |
| **Blender Cycles CPU** | 🐌 30-60s | ★★★★★ | 最终展示用 | 需要时才开，太慢不适合迭代 |

**2026-06新确认的策略：Cura可以充当临时渲染替代**，它导入STL后带实体填充预览，能看到模型轮廓和比例关系，不受GPU限制。与2D线框图互补使用。

## 🔧 工具盘点（首次接到建模任务时主动检查）

**建模开始前，先检查系统中到底有什么可用工具（不只是"写了什么"），避免重复使用错误的工具链。**

```bash
# 核心工具
which blender               # 是否有 Blender
blender --version 2>&1      # 版本

# Python 库
pip3 list 2>/dev/null | grep -iE 'numpy-stl|trimesh|cadquery|pillow|open3d|pyrender|vedo'

# 预览工具
which f3d openscad meshlab  # 快速预览/参数化

# 安装状态（按用户体系）
echo "参数化路线: $(which openscad cadquery 2>/dev/null | tr '\n' ' ')"
echo "STL修复: $(pip3 list 2>/dev/null | grep -i 'trimesh')"
echo "快速预览: $(which f3d 2>/dev/null)"
```

**如果检查发现关键工具缺失，向用户报告缺失清单并建议一次性安装，不要绕路用低效替代方案。**

| 缺失工具 | 安装命令 | 缺失时的影响 |
|---------|---------|------------|
| trimesh | `pip3 install trimesh networkx` | 无法做自动化质检（水密性、体积、组件分析），只能绕 Blender |
| f3d | `brew install f3d` | STL 预览需开 Blender 渲染（3-5s vs 0.5s） |
| openscad | `brew install openscad` | 参数化规则件只能用 Blender 慢慢捏 |
| cadquery | `pip3 install cadquery` | 无 Python 参数化 CAD，几何体全靠 Blender bmesh |
| Meshmixer | 官网下载 | 无专业 STL 修复/分件工具 |

---

## Phase 0: 查工具+定方案（建模前必须执行）

Use this skill when the user wants to **3D print a custom object** — an articulated toy, a functional part, a decorative model — and asks you to create the STL file(s). The approach uses `numpy-stl` to build geometry from basic primitives (sphere, cylinder, cone, extrusion) and export as `.stl` files ready for Bambu Studio / Orca Slicer / Cura.

## When to use this

- User says "design a 3D model of X" or "make something I can print"  
- User has a Bambu Lab / Creality / Prusa / Anykubic FDM printer  
- The model can be **one-piece** (single STL, boolean-UNION merged — preferred for maximum simplicity)  
- Multi-part articulated designs (joints, hinges, snap-fits) — export as separate STL files only if user explicitly asks for movable parts  
- Phone cases (foldable or single-back) using the numpy-stl extrusion pattern  
- The model can be approximated as **combinations of basic geometric shapes** (spheres, cylinders, cones, extrusions) when using numpy-stl  

## Phase 0: Check available tooling FIRST (before modeling anything)

**This is the single most important step and the most common source of wasted iterations.** Before writing a single line of modeling code:

```
1. CHECK what 3D tools are installed on the system:
   which blender          # /Applications/Blender.app → FULL 3D SUITE
   which openscad         # Precision CAD
   pip3 list | grep trimesh  # Mesh analysis + repair
   pip3 list | grep cadquery  # Parametric CAD

2. CHOOSE the right tool for the model class:

   | Model type | Correct tool | Wrong tool (waste of time) |
   |-----------|-------------|---------------------------|
   | | Weapons (guns, swords, mecha) | **Blender bpy — elliptical cross-section stacking (lofting)** (see `references/weapon-side-profile-extrusion.md` and `references/elliptical-lofting-weapon.md`) for side-profile extrusion **OR** elliptical cross-section stacking (better 3D depth, fewer fallbacks required). If the side-profile extrusion produces a flat/stamp-like result (thin slice, user says "看不出立体感"), switch to **elliptical cross-section stacking** (see `references/elliptical-lofting-weapon.md`). | numpy-stl box composition → produces blocky unrecognizable shapes |
   | Characters/animals/organic | **Blender bpy** (subdivision surfaces) | numpy-stl sphere/cylinder combos → faceted, ugly |
   | Phone cases, simple boxes | numpy-stl (fast, no deps) | Blender (overkill startup time) |
   | Multi-part articulated joints | Blender bpy (better tolerance control) | numpy-stl (no boolean ops) |
   | Geometric/angular (buildings, crates) | Either (numpy-stl is faster) | — |

3. **If Blender is installed, USE IT for anything curved/complex.** Weapons, characters, vehicles, and any model where the user says "看不出样子" requires Blender. numpy-stl cannot produce recognizable weapon shapes — period. The box composition technique is only acceptable for: phone cases, simple jewelry boxes, geometric abstract art, or models where the user explicitly says "方块风格就行".

4. **If Blender is NOT installed, install it:**
   brew install --cask blender
   # Then proceed with Blender pathway below

5. **If neither Blender nor numpy-stl can handle the complexity**, tell the user honestly what's possible vs. what needs a professional tool (Fusion 360, Nomad Sculpt, etc.)
```

### 🚨 HARD STOP Signal: When user says the model is unrecognizable

**This is the single most costly waste pattern in 3D modeling — iterating the same approach 3+ times while user keeps saying "看不出来".**

**Hard-stop trigger phrases from this user:**
- "看不出来是枪" / "看不出来是啥东西"
- "都离谱，都看不出来像一把X"
- "没法给你精确的解释哪个地方做的不对"

**Protocol (NO EXCEPTIONS):**
1. **STOP IMMEDIATELY** — do NOT produce another iteration of the same approach
2. **DO NOT ask "what specifically is wrong?"** — the user already told you: the whole thing is unrecognizable, which means the modeling approach itself is wrong, not a detail
3. **Research the alternative modeling approach first** (Phase 0 of systematic-debugging skill)
4. **Switch to a fundamentally different method**, not just tweaked parameters:
   - Box composition → **Side-profile extrusion** (for weapons/mecha)
   - numpy-stl → Blender bmesh (for curved/organic)
   - Blender bmesh → CadQuery/Fusion 360 (for precision parts)
5. Only after the new approach is ready → produce one new version and send

**Common failure pattern (what happened in this user's session):**
```
v1 (780 box-composite faces) → user: "差距太大"
v2 (276 box-composite faces) → user: "看不出枪的样子"
v3 (5712 subdivided box-composite faces, 2× before/after renders) → user: "都离谱"
→ THEN finally switched to side-profile extrusion → v4 (49 faces, correct silhouette)
```
**The problem was never the number of faces or the render quality.** It was the box-composition approach itself — no amount of subdivision makes boxes into a gun silhouette.

### ⚠️ MANDATORY: Analyze reference image BEFORE extracting contours

**🚨 HARD RULE: Before extracting ANY contour from a reference image, use vision_analyze to check what the actual shape IS. Do NOT assume the reference image matches your mental model of the target object.**

**Why this is critical:**
- Bambu AI/MakerWorld point cloud references are **3D surface approximations of photos**, not accurate category-level representations. The AI may generate "a gun" that looks like an energy blade/saber because it doesn't understand object categories.
- Reference images may be rotated (gun pointing "up" instead of forward) or from ambiguous angles
- A "枪" reference may actually be a "刃" (blade) — as happened with FFAR1 "无境空刃" — wasting hours of contour extraction + extrusion work

**Protocol:**

```
1. vision_analyze(ref_image, question="这是[目标物体类别]的参考图吗？提取轮廓会得到什么形状？这个形状和[目标物体]一致吗？")

2. If the visual model says the silhouette does NOT match the target:
   → STOP contour extraction
   → Report finding to user with specific description of what the silhouette actually is
   → Ask user to confirm: "这张参考图的轮廓看起来更像[X]，不是[Y]。你想继续按参考图的形状做，还是用其他参考？"

3. If user confirms it's the right reference despite mismatch:
   → Accept user's judgment and proceed
   → Document the shape discrepancy in modeling notes

4. If user says they have other/cleaner references:
   → Request the new references before starting any modeling
```

**Real case (无境空刃 FFAR1, 2026-06-09):**  The side-view point cloud reference extracted to a maple-leaf/energy-blade silhouette, not a gun shape. Four Python scripts (v3-v4-v5) and hours of iteration were spent before discovering the reference image fundamentally was NOT a gun. The name "空刃" (empty blade) literally describes a blade, not a firearm.

####  Orientation Ambiguity Protocol: When vision models give contradictory answers

**Scenario**: You upload a reference image and ask "which direction is up/forward?" -- different vision_analyze calls give different answers. This happened with FFAR1 where one call said "tip points up-left", another said "tip points right, blade curves down".

**Protocol:**

1. **Do NOT ask about the object's category name** (e.g. "is this a gun?") -- vision models will say "yes" to almost anything if the prompt primes them toward that category.

2. **Ask only about geometry** -- "Where is the sharpest/thickest part? Describe the outline shape without naming it."

3. **Use neutral language** -- "Describe the overall shape and direction of the object in this image. Where does the narrowest part point?"

4. **If answers still contradict** → the reference image is genuinely ambiguous. Do NOT proceed with contour extraction. Instead:
   - Ask the user: "这张参考图的形状我看不太清方向。枪口（最细的一端）应该朝哪个方向？是朝上还是朝前？"
   - Or provide a simple sketch of what the contour looks like and ask user to confirm orientation
   - Better to slow down and ask than to run 4 scripts with wrong orientation

5. **After user confirms orientation** → only then extract contours. Save the confirmed orientation to memory.

### Phase 1: Research the reference object FIRST (critical for game/character models)

**Do NOT start modeling based solely on user-provided photos or AI-generated references.** AI-generated references (Bambu Studio AI, MakerWorld point clouds) can produce fundamentally wrong silhouettes — see `references/ai-generated-reference-ambiguity.md` for the full detection protocol.

**Do NOT start modeling based solely on user-provided photos.** User photos are often ambiguous, poorly lit, or from unrecognizable angles. Especially common pitfalls:
- User says "it's a gun" but the photos are of **Space Engineers spaceships** that only vaguely resemble a gun
- User knows the in-game name (e.g. "无境空刃" = FFAR1 mythic skin from CODM) but the photos they took don't match
- The object is a **licensed game skin/character** with detailed official reference available online

### ⚠️ Critical: User photos may show a COMPLETELY WRONG object

**Also critical: AI-generated reference images (Bambu Studio AI, MakerWorld) can produce fundamentally ambiguous silhouettes.** The AI doesn't understand the object category — it generates a 3D surface approximation of the input photo. A reference image described as "a gun" may actually be an energy blade/saber shape. See `references/ai-generated-reference-ambiguity.md` for the full pattern, detection protocol, and hard rules.

### ⚠️ Critical: User photos may show a COMPLETELY WRONG object

**This is the single most common reason for wasted iterations in 3D modeling.** User-provided photos are often NOT of the object they want modeled. Real scenario from this user's history: a child sent 6 photos of Space Engineers spaceships saying "help me make a 3D model", said it was "a gun" when asked, and only later revealed the actual object was a CODM weapon skin — the photos were completely unrelated spaceships.

**Protocol when photos seem wrong:**

1. **SUSPECT ISOLATION**: If the photos show something that looks like a different category (spaceship vs. gun, movie character vs. real person, abstract vs. recognizable), DO NOT assume the user knows what they sent.
2. **DIRECT VERIFICATION**: Ask explicitly: "你发的这几张图确实是你想要的那个的模型截图吗？还是这是你在别处找的参考图？"
3. **WHEN USER ADMITS UNCERTAINTY** (they'll say "难度极其大" "可能不清晰"): Follow Bilibili research workflow; their photos are secondary at best.
4. **WHEN USER INSISTS it's correct**: Accept their word but mention online reference looks different — offer to re-model if first attempt doesn't match.

**Signals the user's photos are likely wrong:** User says "难度极其大" about modeling, photos show different geometry than known game skin, user says "去上网搜索，因为我的三视图可能不清晰", photos from game screenshot (not 3D viewer), child/kid profile user.

### Research workflow

```
1. ASK the user for the exact name of the object (in-game name, brand, series)
2. SEARCH Chinese gaming platforms first (Bilibili is best for CODM/Genshin/etc. — bypasses Baidu/Google CAPTCHA)
   → Search Bilibili: https://search.bilibili.com/all?keyword=<name>
   → Look for: 4K展示/无UI/检视换弹 videos (clean display videos without UI overlay)
   → Also search: 纸板手工/手工制作 (papercraft videos show solid understanding of structure)
3. CAPTURE video cover images as visual reference:
   - Extract image URLs from Bilibili search results via browser_get_images
   - Analyze multiple covers with vision_analyze to build 3D understanding
   - Prioritize: 4K展示 > 游戏内截图 > 转盘预告 > 手工还原
4. For each image, ask vision_analyze specifically about:
   - Overall shape and silhouette
   - Color distribution (primary + accent)
   - Structural parts: barrel, grip, stock, magazine, muzzle device
   - Special effects (glow, particles, animated elements — note these for aesthetics, skip for STL)
5. Triangulate: Compare ALL available references before building — the user's original photos + at least 2-3 online reference images
6. Only then start geometry building
- Child user (kid profile) sending photos | Higher likelihood of proxy references; ask for exact name |

### Reference types prioritized

| Source | Quality | Availability |
|--------|---------|-------------|
| Bilibili 4K无UI展示视频封面 | ★★★★★ | Always (no CAPTCHA) |
| Bilibili 纸板手工视频封面 | ★★★★☆ | Shows physical structure |
| Official concept art / key art | ★★★★★ | Often behind Baidu CAPTCHA |
| Game wiki pages | ★★★☆☆ | May need CAPTCHA |
| In-game screenshots (user-provided) | ★★★☆☆ | Depend on user's phone quality |
| YouTube thumbnails | ★★★★☆ | Good when Bilibili doesn't have it |

## Default: prefer one-piece over multi-part

If the user doesn't specify, **default to a single STL file** with all parts fused. Only split into multiple files if the user explicitly asks for articulated/movable parts. This avoids post-print assembly and support-structure issues.

## When NOT to use this

- User wants **mechanical CAD** with exact tolerances — recommend Fusion 360 / OnShape / FreeCAD
- User wants **multi-material / color 3D printing** — handle separately, this skill only covers single-material STL output
- User wants **sculpted organic models without Blender installed** — install Blender first (`brew install --cask blender`), then proceed with the Blender boolean UNION section below

> **NOTE**: Organic/sculpted models (animals, characters, toys) are fully within scope — use the **Blender pathway** with boolean UNION for one-piece output. Blender is the preferred tool for this class of work; numpy-stl primitives alone cannot produce smooth character models.

## Setup

```bash
pip3 install numpy-stl Pillow
```

## Core technique: building STL from Python

### 1. Fundamental geometry builders

Define helper functions in your script for the five essential shapes:

| Shape | Parameters | Use for |
|-------|-----------|---------|
| **Sphere** | `radius, cx, cy, cz, lat_steps, lon_steps` | Heads, joints, rounded corners |
| **Cylinder** | `radius, height, cx, cy, cz, n` | Legs, arms, axles |
| **Cone (frustum)** | `radius_bottom, radius_top, height, cx, cy, cz, n` | Ears, tapered limbs, tail segments |
| **Extrusion** | `points_xy, z0, z1` | Custom 2D shapes pulled into 3D |
| **Ellipsoid** | `radius_x, radius_y, radius_z` (stretch a sphere) | Bodies, eggs, capsules |

### 2. Mesh building and manipulation

```python
def _make_mesh(verts, faces):
    m = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            m.vectors[i][j] = verts[f[j]]
    return m

def _merge_meshes(meshes):
    """Combine multiple meshes into one STL"""
    total = sum(len(m.vectors) for m in meshes)
    combined = mesh.Mesh(np.zeros(total, dtype=mesh.Mesh.dtype))
    idx = 0
    for m in meshes:
        combined.vectors[idx:idx + len(m.vectors)] = m.vectors
        idx += len(m.vectors)
    return combined

def _translate(m, dx=0, dy=0, dz=0):
    m.vectors += np.array([dx, dy, dz])
    return m

def _rotate_y(m, angle_deg, cx=0, cy=0, cz=0):
    """Rotate around Y axis (forward/backward swing for legs)"""
    angle = math.radians(angle_deg)
    c, s = math.cos(angle), math.sin(angle)
    m.vectors -= np.array([cx, cy, cz])
    for i in range(len(m.vectors)):
        x, y, z = m.vectors[i].T
        m.vectors[i].T[0] = x * c + z * s
        m.vectors[i].T[2] = -x * s + z * c
    m.vectors += np.array([cx, cy, cz])
    return m
```

### 4b. Box-primitive composition for weapon/mecha/geometric models

**Use when**: Building models with flat-sided geometry — guns, weapons, mecha, robots, vehicles, architectural forms, or any object where straight lines and right angles dominate.

This is a **pure numpy-stl** technique (no Blender needed, no sphere/cylinder math) that builds everything from rectangular boxes:

```python
def box_mesh(sx, sy, sz, cx, cy, cz):
    """Generate a solid rectangular box mesh centered at (cx,cy,cz)"""
    sx2, sy2, sz2 = sx/2, sy/2, sz/2
    pts = np.array([
        [cx-sx2, cy-sy2, cz-sz2], [cx+sx2, cy-sy2, cz-sz2],
        [cx+sx2, cy+sy2, cz-sz2], [cx-sx2, cy+sy2, cz-sz2],
        [cx-sx2, cy-sy2, cz+sz2], [cx+sx2, cy-sy2, cz+sz2],
        [cx+sx2, cy+sy2, cz+sz2], [cx-sx2, cy+sy2, cz+sz2],
    ])
    faces = np.array([
        [0,1,2],[0,2,3],[4,6,5],[4,7,6],
        [0,5,1],[0,4,5],[2,6,7],[2,7,3],
        [0,3,7],[0,7,4],[1,5,6],[1,2,6],
    ])
    m = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, fi in enumerate(faces):
        for j in range(3):
            m.vectors[i][j] = pts[fi[j]]
    return m

def add_box(parts, sx, sy, sz, cx=0, cy=0, cz=0):
    """Add a box to a parts list for later combine()"""
    parts.append(box_mesh(sx, sy, sz, cx, cy, cz))

def combine(parts):
    """Merge a list of meshes into one STL"""
    total = sum(len(m.vectors) for m in parts)
    c = mesh.Mesh(np.zeros(total, dtype=mesh.Mesh.dtype))
    off = 0
    for m in parts:
        n = len(m.vectors)
        c.vectors[off:off+n] = m.vectors
        off += n
    return c
```

**Design pattern (weapon model example):**

```python
def build():
    parts = []
    # Coordinate convention: Y = long axis (forward/barrel), X = width, Z = thickness
    
    # === BARREL (Y: 1.8 to 5.2) ===
    add_box(parts, 0.26, 3.4, 0.26, 0, 3.4, 0)      # main barrel
    add_box(parts, 0.30, 0.4, 0.30, 0, 4.6, 0)       # flared end
    add_box(parts, 0.52, 0.06, 0.52, 0, 4.8, 0)      # muzzle ring
    
    # barrel vent ridges (repeat pattern along Y)
    for i in range(5):
        y = 2.2 + i * 0.45
        add_box(parts, 0.34, 0.04, 0.08, 0.20, y, 0)
        add_box(parts, 0.34, 0.04, 0.08, -0.20, y, 0)
    
    # === HANDGUARD (Y: 1.0 to 2.8) ===
    add_box(parts, 0.60, 1.8, 0.50, 0, 1.9, 0)
    # top rail
    add_box(parts, 0.44, 1.4, 0.10, 0, 2.0, 0.30)
    # side grooves
    for i in range(6):
        y = 1.15 + i * 0.25
        add_box(parts, 0.44, 0.02, 0.06, 0, y, 0.30)
    
    # === RECEIVER (Y: -0.3 to 1.2) ===
    add_box(parts, 0.60, 1.5, 0.56, 0, 0.4, 0)
    add_box(parts, 0.08, 0.9, 0.06, 0, 0.5, 0.36)   # top rail
    add_box(parts, 0.12, 0.20, 0.04, 0.22, 0.6, 0.34)  # ejection port
    
    # === GRIP (Y: -0.8 to 0.0) — stepped blocks ===
    for i in range(6):
        yp = -0.65 + i * 0.12
        w = 0.26 - i * 0.01
        add_box(parts, w, 0.10, 0.30, 0.05 + (-0.02)*(i+1), yp, 0)
    
    # === MAGAZINE (Y: -0.9 to -0.3) ===
    add_box(parts, 0.28, 0.55, 0.24, 0, -0.60, 0)
    add_box(parts, 0.32, 0.05, 0.28, 0, -0.88, 0)  # mag bottom
    
    # === STOCK (Y: -2.2 to -0.4) ===
    add_box(parts, 0.38, 1.4, 0.24, 0, -1.5, 0)
    add_box(parts, 0.44, 0.10, 0.30, 0, -2.2, 0)  # butt plate
    
    return parts

parts = build()
combined = combine(parts)

# Center and scale to ~85mm
combined.vectors -= combined.vectors.mean(axis=(0, 1))
mx = np.max(np.abs(combined.vectors))
combined.vectors *= 42.5 / mx  # half of target length

combined.save('weapon.stl')
```

**When to use box composition vs sphere/cylinder:**

| Approach | Best for | Example models |
|----------|----------|---------------|
| **Box composition** | Geometric/flat-sided shapes | Guns, vehicles, buildings, mecha, tools |
| **Sphere/cylinder** | Organic/smooth shapes | Animals, characters, toys, ergonomic grips |
| **Hybrid** | Combination objects | Gun with organic grip (box for barrel, cylinder/cone for grip) |

**Key advantages of box composition:**
- Zero math — just pick (sx, sy, sz) dimensions and (cx, cy, cz) placement
- Easy to iterate — adjust a single number and regenerate
- Naturally FDM-friendly (flat faces minimize overhangs)
- Runs in pure numpy-stl, no Blender, no trimesh, no heavy deps
- Fast even for many parts (89 boxes = ~1068 faces, 52KB STL)

**Limitations:**
- No curved surfaces — all faces are flat
- Overlapping boxes create internal faces (not manifold — but FDM can still print them)
- Cannot do boolean operations (composite parts sit inside each other)
- Preview via 2D point cloud is rough — visual AI cannot recognize the shape from point cloud alone; user must view STL directly

### 5. Multi-part articulated design pattern

For movable-joint models (articulated toys, action figures):

```
Model structure:
├── body (fixed, single piece)
├── head (socket-fit on body, rotates)
├── front_left / front_right (cylindrical joint, swings)
├── rear_left / rear_right (cylindrical joint, swings)
└── tail (optional)

Joint gap: GAP = 0.4mm (standard nozzle width)
```

**Key design rules:**
- Each movable part is a **separate STL file**
- Joints use a **cylinder-in-socket** design: subtract GAP from the peg, add GAP to the socket
- Align parts so they sit flush on the print bed (no overhangs → no supports)
- Target total assembled size: ~50-100mm for desktop FDM printers

### 4. STL export

```python
from stl import Mode

def export_stl(parts_dict, output_dir):
    for name, part_mesh in parts_dict.items():
        path = os.path.join(output_dir, f"{name}.stl")
        part_mesh.save(path, mode=Mode.BINARY)
    
    # Also export assembled reference
    combined = _merge_meshes(list(parts_dict.values()))
    combined.save(os.path.join(output_dir, "assembled.stl"))
```

### 5. Preview image generation

Use Pillow to generate a **2D annotated preview** with:
- **Front view** (face-on): show face features, legs, tail
- **Side view** (profile): show body proportions, leg positions
- **Top view** (plan): show width proportions, ear positions
- Metadata panel: file list, dimensions, print settings, assembly instructions

**Preferred workflow**: Always use the reusable `scripts/stl_2d_preview.py` script for preview generation. It reads binary STL directly, projects triangles onto 2D planes (front/side/top/iso), and draws with PIL. No Blender startup overhead.

```bash
# Quick preview:
python3 /path/to/skills/creative/3d-printing/scripts/stl_2d_preview.py model.stl --output-prefix preview

# All 4 views:
python3 stl_2d_preview.py model.stl -o model -v front side top iso

# For large files (>20K triangles), sample 10%:
python3 stl_2d_preview.py model.stl --sample 0.1 -o model
```

**Why prefer 2D line-art over Blender EEVEE rendering for headless:**
Even with correct camera Euler angles, proper lighting (3+ area lights), bright red/blue materials, and light background, Blender headless EEVEE renders on Mac Mini M4 (16GB, no dedicated GPU) produce **uniformly flat gray images** that AI vision cannot identify. The 2D line-art approach consistently produces recognizable outlines regardless of GPU or headless mode limitations. **For weapon/mecha models, use `stl_2d_preview.py` as the primary preview method** and only fall back to Blender EEVEE for color/texture previews if the user specifically requests them.

### 6. One-piece character/organic model via Blender（布尔 UNION 一体式）

**Use when**: User wants a single STL file with all body parts fused (no assembly, no separate files). This replaces the multi-part articulated pattern when the user says "一体打印" or complains about parts not connecting.

**Core philosophy**: Build each body part as a separate Blender primitive (sphere, cylinder, box), then UNION-merge them all into one mesh, add a flat base plate, export single STL.

#### Workflow

```
1. Build parts as separate primitive objects (BMesh or bpy.ops)
   ├── body/head/neck (spheres, ellipsoids)
   ├── legs (spheres/cylinders placed overlapping the body)
   ├── accessories (mask, eyes, mouth, ridges)
   └── tail (elongated ellipsoid)
2. Iterative boolean UNION (merge parts[0] with parts[1:N])
3. Clean up: remove_doubles → recalc normals → fill holes
4. Add flat base plate (rectangle covering XY footprint at Z=-2 to Z=2.5)
5. Translate everything to Z=0 (subtract min_z from all vertices)
6. Export single STL (`bpy.ops.wm.stl_export`)
7. Render preview
```

#### Key design rules

| Rule | Why | How |
|------|-----|-----|
| **Overlap every part** with the body | Boolean UNION only works on intersecting volumes | Place legs/head/tail so their bounding boxes overlap the body by 5-15mm |
| **Add a flat base plate** | Guarantees Z=0 bed adhesion, no supports needed | UNION a thin box (-2 to 2.5mm Z) covering the full XY extent, then translate Z=0 |
| **One single STL file** | User can just slice and print | Don't export separate files unless user explicitly asks for multi-part |
| **Use enough segments (24-32)** for spheres | Smooth organic look | segs=24 for body, 16-20 for accessories to balance file size vs quality |
| **Avoid thin/small protruding parts** | They break off during boolean or become fragile to print | Keep smallest dimension ≥ 3mm, or merge into a thicker base |

#### Blender 5.x boolean solver notes

```python
# WRONG — 'FAST' removed in Blender 5.x
bool_mod.solver = 'FAST'

# RIGHT — use FLOAT (fast, float-precision)
bool_mod.solver = 'FLOAT'
# Alternatives: 'EXACT' (slow, precise), 'MANIFOLD' (slow, best quality)
```

#### Blender 5.x EEVEE removed attributes

These were valid in Blender 4.x but cause `AttributeError` in 5.x:
- `scene.eevee.use_gtao` — removed
- `scene.eevee.use_volumetric` — removed
- `scene.eevee.use_bloom` — removed
- `scene.eevee.taa_render_samples` — still valid

Simplify EEVEE setup to only set what exists:
```python
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1200
scene.render.resolution_y = 800
scene.eevee.taa_render_samples = 32  # still valid in 5.x
# Skip use_gtao, use_volumetric, use_bloom — all removed
```

## Print settings to include in output

```
🖨️ Recommended FDM settings
  • Material: PLA or PETG
  • Nozzle: 0.4mm
  • Layer height: 0.2mm
  • Infill: 15-20%
  • Supports: NONE (design parts to be support-free)
  • Bed adhesion: Brim (optional, for tall thin parts)
  • Joint gap: 0.4mm (print ready, no post-processing needed)
```

## Typical script structure

```python
import numpy as np
from stl import mesh
import math, os
from PIL import Image, ImageDraw, ImageFont

# 1. Define geometry helpers (sphere, cylinder, cone, extrude, merge, translate, rotate)
# 2. Build each part as a function
# 3. Export STLs
# 4. Generate preview image
# 5. Print file list and instructions
```

### 手机壳/保护壳建模 (Phone Case Modeling)

这个模式适用于用户想要 **3D 打印手机壳**——折叠屏或直板机，分体式或一体式。

**两种技术路线：**
| 场景 | 推荐路线 |
|------|---------|
| 精确尺寸的简单壳（圆角矩形+挖孔） | **numpy-stl 全 Python 生成**（见下文） |
| 复杂造型（曲线、纹路、装饰突起） | **Blender bpy**（见"Blender pathway"节） |
| 先验证再精修 | numpy-stl 生成基础 → Blender 精修 |

### numpy-stl 手机壳生成模式（简化路线）

当模型是一个**圆角矩形 + 内腔 + 摄像头孔**的标准手机壳时，**完全不需要 Blender**。用 numpy-stl 纯 Python 即可：

```python
import numpy as np
from stl import mesh
import math, os

def rounded_rect_profile(width, height, radius, n=32):
    \"\"\"生成圆角矩形轮廓点（Z=0 平面，逆时针）\"\"\"
    r = radius
    w2, h2 = width/2, height/2
    pts = []
    # 四段圆弧：右上→左上→左下→右下
    for cx, cy, a_start in [(w2-r, h2-r, 0), (-w2+r, h2-r, math.pi/2),
                              (-w2+r, -h2+r, math.pi), (w2-r, -h2+r, 3*math.pi/2)]:
        for i in range(n):
            a = a_start + (math.pi/2) * i / n
            pts.append((cx + r*math.cos(a), cy + r*math.sin(a), 0.0))
    return pts

def extrude_to_stl(profile_pts, z0, z1):
    \"\"\"将 2D 轮廓挤出为 3D STL\"\"\"
    n = len(profile_pts)
    verts = np.array([[x, y, z0] for x, y, _ in profile_pts] +
                      [[x, y, z1] for x, y, _ in profile_pts], dtype=np.float64)
    faces = []
    # 底面（逆时针）和顶面（顺时针）
    faces.append(list(range(n)))                     # 底面
    faces.append(list(range(n, 2*n))[::-1])          # 顶面
    for i in range(n):                                # 侧面四边形
        j = (i + 1) % n
        faces.append([i, j, j+n, i+n])
    
    triangles = []
    for f in faces:
        for i in range(1, len(f)-1):
            triangles.append([f[0], f[i], f[i+1]])
    
    m = mesh.Mesh(np.zeros(len(triangles), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(triangles):
        for j in range(3):
            m.vectors[i][j] = verts[tri[j]]
    return m

def build_phone_case(w=146, h=160, corner_r=8, wall=1.5, tolerance=0.3,
                     cam_diam=36.0, cam_rise=5.0, z_bot=0, z_top=9.7):
    \"\"\"生成完整单面后盖\"\"\"
    # 外壳轮廓
    outer = rounded_rect_profile(w, h, corner_r)
    outer_mesh = extrude_to_stl(outer, z_bot, z_top)
    
    # 内腔轮廓（缩小 wall+tolerance）
    inner_w, inner_h = w - 2*(wall+tolerance), h - 2*(wall+tolerance)
    inner_r = max(corner_r - (wall+tolerance), 1.0)
    inner = rounded_rect_profile(inner_w, inner_h, inner_r)
    inner_mesh = extrude_to_stl(inner, z_bot + wall, z_top - wall)
    
    # 组合
    from stl import mesh as stl_mesh
    def merge(m1, m2):
        combined = stl_mesh.Mesh(np.concatenate([m1.data, m2.data]))
        return combined
    
    case = merge(outer_mesh, inner_mesh)
    
    # 摄像头孔环（在顶面上凸起）
    cd = cam_diam / 2
    segs = 48
    ring_outer_verts = [(cd + 1.0 + cd*math.cos(a), cd*math.sin(a), z_top)
                        for i in range(segs) for a in [2*math.pi*i/segs]]
    ring_inner_verts = [(cd - 0.5 + cd*math.cos(a), cd*math.sin(a), z_top + cam_rise)
                        for i in range(segs) for a in [2*math.pi*i/segs]]
    # ... 构建环的三角面（圆环体展开）
    
    return case
```

**关键优势：** 不依赖 Blender，5 秒生成完毕，STL 文件控制在 100-300KB，三角面最少化（~5000 面）。

> 完整可运行的代码示例和验证脚本见 `references/numpy-stl-phone-case.md`

### 关键尺寸推算

当找不到官方发布的长×宽时，从已知参数推算：

```python
# 已知：对角线尺寸（英寸）、分辨率（像素）
# 求：物理长宽（mm）
import math

diag_inch = 8.12  # 内屏对角线
res_x, res_y = 2480, 2248  # 分辨率
ppi_diag = math.sqrt(res_x**2 + res_y**2) / diag_inch
width_mm = res_x / ppi_diag * 25.4
height_mm = res_y / ppi_diag * 25.4
# 展开态机身 ≈ 屏幕宽高 + 边框 (约 2-3mm 每边)
phone_w = width_mm + 4   # ≈146mm
phone_h = height_mm + 4  # ≈133mm
```

### 分体式折叠手机壳设计模式

| 组件 | 说明 |
|------|------|
| **左半壳** | 外屏侧，平整面，160mm × 73mm × 8.93mm |
| **右半壳** | 内屏背侧，带圆形摄像头孔位+凸起装饰圈 |
| **两半间隙** | 2mm（保证折叠不卡） |
| **壁厚** | 1.2mm |
| **内腔公差** | 0.3mm（手机放入不紧不松） |

### 核心建模技巧

#### 1. 圆角矩形轮廓 (手机壳基础)

```python
import bmesh, math

def make_rounded_rect(width, height, radius, verts=32):
    """生成圆角矩形轮廓 BMesh 顶点"""
    r = radius
    w2, h2 = width / 2, height / 2
    n = max(8, verts // 4)
    pts = []
    for angle_start in [math.pi/2, math.pi, 3*math.pi/2, 0]:
        for i in range(n):
            a = angle_start + (math.pi/2 * i / n)
            sign_x = -1 if angle_start in (math.pi, 3*math.pi/2) else 1
            sign_y = -1 if angle_start >= math.pi else 1
            x = sign_x * (w2 - r) + r * math.cos(a)
            y = sign_y * (h2 - r) + r * math.sin(a)
            pts.append((x, y))
    return pts
```

#### 2. 外形体构建 (双圆角矩形 loft)

```python
def build_lofted_body(bm, bot_pts, top_pts, z_bot, z_top, pos_x=0):
    """两个圆角矩形轮廓 → 带侧面连接的实体"""
    bot = [bm.verts.new((x + pos_x, y, z_bot)) for x, y in bot_pts]
    top = [bm.verts.new((x + pos_x, y, z_top)) for x, y in top_pts]
    n = len(bot)
    bm.faces.new(bot)          # 底面
    bm.faces.new(top)          # 顶面
    for i in range(n):          # 侧面四边形
        j = (i + 1) % n
        bm.faces.new([bot[i], bot[j], top[j], top[i]])
```

#### 3. 内腔挖空 (Boolean DIFFERENCE)

```python
# 外壳体对象 outer_obj
# 内腔体对象 inner_obj (比外壳小壁厚)
bpy.context.view_layer.objects.active = outer_obj
outer_obj.select_set(True)
# Blender 5.x 中 modifier 名称是英文
bpy.ops.object.modifier_add(type='BOOLEAN')
mod = outer_obj.modifiers['Boolean']    # 不是 '布尔'
mod.operation = 'DIFFERENCE'
mod.object = inner_obj
bpy.ops.object.modifier_apply(modifier=mod.name)
```

#### 4. 摄像头凸起装饰圈

```python
# 使用内外两个圆环，在壳表面上方构建环形凸起
r_outer = cam_diam/2 + 1.0
r_inner = cam_diam/2 + 0.3
ring_h = 2.0  # 凸起高度
segs = 48

obot = [bm.verts.new((cx + r_outer*cos(a), cy + r_outer*sin(a), z_surface))
        for i in range(segs)]
otop = [bm.verts.new((v.co.x, v.co.y, z_surface + ring_h)) for v in obot]
itop = [bm.verts.new((cx + r_inner*cos(a), cy + r_inner*sin(a), z_surface + ring_h))
        for i in range(segs)]
ibot = [bm.verts.new((v.co.x, v.co.y, z_surface - 0.5)) for v in itop]

# 顶面环 (otop→itop)，外侧面 (obot→otop)，内侧面 (itop→ibot)，底面环 (ibot→obot)
```

#### 5. 整体合并

用 `Boolean UNION` 将摄像头装饰圈合并到主壳体，然后应用 Bevel 修改器倒角。

### 打印建议

- **材料**: TPU（柔性，易安装拆卸）或 PETG（刚性）
- **朝向**: 摄像头孔朝上，树状支撑
- **层高**: 0.2mm
- **填充**: 15-20%

---

## Blender pathway (for organic/sculpted models)

When Blender is installed (`brew install --cask blender`), use it for models that need **subdivision surfaces, curves, smooth contours, or organic shapes** that basic numpy-stl primitives cannot approximate well.

### Setup

```bash
brew install --cask blender        # Installs to /Applications/Blender.app
which blender                       # /opt/homebrew/bin/blender
blender --background --version      # Verify Python API works
```

Test the Python API:
```bash
blender --background --python-expr "
import bpy
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0))
print('Blender Python API OK')
" 2>&1 | tail -3
```

### Typical workflow

1. **Write a Python script** that uses Blender's bpy module
2. **Run headless**: `blender --background --python your_script.py`
3. **Export STL per part** using `bpy.ops.wm.stl_export()`

### Key Blender 5.x API notes (see references/blender-5.1-api.md for full details)

- **STL export** (Blender 5.0+): `bpy.ops.wm.stl_export(filepath=..., export_selected_objects=True, ascii_format=False, global_scale=10.0)` — note: no `scale_unit` parameter (removed in 5.x)
- **Render engine** (Blender 5.0+): `bpy.context.scene.render.engine = 'BLENDER_EEVEE'` (was `'EEVEE'` before 5.0)
- **Subdivision Surface modifier**: Use `SUBSURF` type, levels=1 for 3D printing (levels=2 creates very large STL files)
- **Curve to mesh**: Create a curve, set `bevel_depth` and `bevel_resolution` for tube geometry, then `bpy.ops.object.convert(target='MESH')`
- **Material API deprecation**: `mat.use_nodes = True` will be removed in Blender 6.0 (currently a DeprecationWarning)

### Blender script structure for multi-part models

```python
import bpy
import math
import os

OUTPUT_DIR = "~/prints/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper: create a part with subdivision surface
def create_part(name, obj, subsurf_levels=1):
    obj.name = name
    obj.data.name = name
    mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    mod.levels = subsurf_levels
    mod.render_levels = subsurf_levels
    # Smooth shading
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj

# Build geometry (spheres, cylinders, cones, curves, etc.)
# Export per-part STLs
def export_stl(obj, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # Apply subdivision modifiers before export
    for mod in obj.modifiers:
        if mod.type == 'SUBSURF':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.wm.stl_export(
        filepath=filepath,
        export_selected_objects=True,
        ascii_format=False,
        global_scale=10.0
    )
```

### Key advantages over numpy-stl

| Feature | numpy-stl | Blender bpy |
|---------|-----------|-------------|
| Surface quality | Faceted (polygon segments) | Smooth (subdivision surfaces) |
| Curves | Hand-made segment chains | Real Bezier curves |
| Organic shapes | Sphere/cylinder combos | Subdivision modeling |
| File size efficiency | High (facets = many triangles) | Lower (subdiv hides base mesh) |
| Render preview | Pillow 2D drawing | EEVEE/Cycles 3D render |
| Learning curve | Simple Python | Blender API complexity |

### Pitfalls

- **STL export params**: Blender 5.x removed `scale_unit` from `wm.stl_export`. Use only `global_scale` (10.0 = mm).
- **Render engine enum**: `'EEVEE'` → `'BLENDER_EEVEE'` in Blender 5.x.
- **Subdivision level**: level 2 creates 4× the triangles of level 1. For 3D printing, level 1 is usually sufficient (the printer can't resolve finer than 0.1mm anyway).
- **Curve objects are not mesh**: You must `bpy.ops.object.convert(target='MESH')` before applying subdivision or exporting STL. Curves don't have `.data.polygons`.
- **Script CPU**: Blender scripts run in a full Blender executable. Each invocation takes 5-10s startup overhead. Batch all operations into one script.
- **Camera framing**: When rendering previews, ensure camera is far enough. A model built with subdivision surfacing is physically larger than its base mesh. Rule of thumb: multiply camera distance by 2× from what feels right — Blender's default camera often clips the model. Test by rendering one quick frame before batch-rendering multiple angles.

---

## Blender 进阶建模技巧

### 1. BMesh — 快速网格构建

`bmesh` 比 `bpy.ops.mesh.*` 快得多，适合在脚本中创建复杂几何体：

#### ⚠️ Blender headless 下的BMesh关键模式：subdivide替代SUBSURF modifier

在Blender headless模式（`blender --background --python ...`）中，**任何modifier的apply操作可能静默失败**——包括SUBSURF(细分曲面)、MIRROR(镜像)、BOOLEAN(布尔)、ARRAY(阵列)。Modifier"应用"前后的模型完全相同，但无报错。这是Blender 5.x在headless模式下已知的行为。

**替代方案：使用bmesh直接操作顶点/边/面进行细化和对称复制，完全不依赖modifier。**

```python
import bpy
import bmesh
import math
import numpy as np

def bmesh_subdivide_for_smoothness(obj, iterations=2, use_smooth=True):
    \"\"\"
    替代SUBSURF modifier的bmesh subdivide方案。
    通过bmesh.subdivide_edges循环细分，直接在网格几何体上增加面数。
    效果等同SUBSURF levels=1~2，但无需modifier apply。
    
    Args:
        obj: Blender mesh object
        iterations: 细分次数。1次≈4x面数，2次≈16x面数
        use_smooth: 是否设置平滑着色
    \"\"\"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    bm.edges.ensure_lookup_table()
    
    for _ in range(iterations):
        edges = list(bm.edges)
        bmesh.ops.subdivide_edges(
            bm,
            edges=edges,
            cuts=1,              # 每条边切1刀 → 面数4x
            smooth=0.0,          # 不偏移顶点位置
            fractal=0.0,
            use_smooth_even=True
        )
        bm.edges.ensure_lookup_table()
    
    bmesh.update_edit_mesh(me)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    if use_smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj

def bmesh_symmetrize_mirror(obj, mirror_axis='X'):
    \"\"\"
    替代MIRROR modifier的bmesh手动镜像方案。
    只建左半侧 → 复制顶点并镜像到右侧 → 合并。
    这需要在建模脚本中就只生成左半侧顶点(X<=0)。
    \"\"\"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    
    axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[mirror_axis]
    original_verts = list(bm.verts)
    
    mirror_map = {}
    for v in original_verts:
        co = v.co.copy()
        if abs(co[axis_idx]) > 0.001:
            new_co = co.copy()
            new_co[axis_idx] = -new_co[axis_idx]
            mirror_map[v] = bm.verts.new(new_co)
    
    # 复制边
    for e in list(bm.edges):
        v1, v2 = e.verts
        if v1 in mirror_map and v2 in mirror_map:
            bm.edges.new([mirror_map[v1], mirror_map[v2]])
        elif v1 in mirror_map:
            bm.edges.new([mirror_map[v1], v2])
        elif v2 in mirror_map:
            bm.edges.new([v1, mirror_map[v2]])
    
    # 复制面（翻转法线）
    for f in list(bm.faces):
        new_fv = []
        flip = False
        for v in f.verts:
            if v in mirror_map:
                new_fv.append(mirror_map[v])
                flip = True
            else:
                new_fv.append(v)
        if len(new_fv) >= 3:
            try:
                bm.faces.new(list(reversed(new_fv)) if flip else new_fv)
            except ValueError:
                pass
    
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.001)
    bmesh.update_edit_mesh(me)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj
```

**适用场景：**

| modifier | bmesh替代方案 | 适用 | 
|----------|-------------|------|
| SUBSURF | `bmesh_subdivide_for_smoothness(obj, iterations=N)` | 提面数、平滑网格 |
| MIRROR | `bmesh_symmetrize_mirror(obj)` | 左右对称，需先在脚本中只建左半侧 |
| BOOLEAN (UNION/DIFFERENCE) | `bmesh.ops.bisect_plane` + 手动三角剖分 | 复杂，建议把零件合并写在一个脚本中避免布尔 |
| BEVEL | `bmesh.ops.bevel(bm, geom=[e for e in bm.edges], offset=0.5, segments=4)` | 倒角 |

**面数控制经验（以武器模型为例）：**
- 基础形状：圆柱/圆锥使用 `segments=24-32`（不是默认的16）
- subdivide 1次：4x面数（24 segments → ~96 segments，足够平滑）
- subdivide 2次：16x面数（谨慎使用，可能50K+面）
- 目标：武器模型 3000-5000 三角面，角色模型 5000-8000 三角面
- 超过1万面 = STL文件 500KB+，对IM传输不友好

`bmesh` 比 `bpy.ops.mesh.*` 快得多，适合在脚本中创建复杂几何体：

```python
import bpy
import bmesh
import math

def create_complex_shape():
    """用 BMesh 构建复杂网格，比 bpy.ops 快 10x+"""
    mesh = bpy.data.meshes.new("ComplexShape")
    bm = bmesh.new()
    
    # 批量创建顶点
    verts = []
    for i in range(24):
        angle = 2 * math.pi * i / 24
        verts.append(bm.verts.new((math.cos(angle), math.sin(angle), 0)))
    
    # 创建面
    for i in range(len(verts)):
        bm.faces.new([verts[i], verts[(i+1) % len(verts)], bm.verts.new((0, 0, 0))])
    
    # 一次性写回 mesh
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new("Shape", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def make_watertight(obj):
    """使用 bmesh 修复 manifold 问题（不依赖 3D Print Toolbox）"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    
    # 合并重合顶点
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    # 重新计算法线向外
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # 填充孔洞
    bmesh.ops.holes_fill(bm, edges=bm.edges[:])
    
    bmesh.update_edit_mesh(me)
    bpy.ops.object.mode_set(mode='OBJECT')

def is_watertight(obj):
    """用 BMesh 检查 mesh 是否水密（不依赖插件）"""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    for edge in bm.edges:
        if not edge.is_manifold:
            bm.free()
            return False
    bm.free()
    return True
```

### 2. Geometry Nodes 脚本化

可以在 Python 中完全创建和驱动几何节点组，适合非破坏性参数化建模：

```python
import bpy

def create_gn_modifier(obj):
    """为对象添加一个 Python 驱动的几何节点修改器"""
    # 创建节点组
    node_group = bpy.data.node_groups.new(name="ParametricGN", type='GeometryNodeTree')
    
    # 添加节点
    group_input = node_group.nodes.new('NodeGroupInput')
    group_output = node_group.nodes.new('NodeGroupOutput')
    mesh_circle = node_group.nodes.new('GeometryNodeMeshCircle')
    set_material = node_group.nodes.new('GeometryNodeSetMaterial')
    
    # 连接节点
    links = node_group.links
    links.new(group_input.outputs['Geometry'], mesh_circle.inputs['Vertices'])
    links.new(mesh_circle.outputs['Mesh'], set_material.inputs['Geometry'])
    links.new(set_material.outputs['Geometry'], group_output.inputs['Geometry'])
    
    # 添加修改器
    mod = obj.modifiers.new(name="MyGN", type='NODES')
    mod.node_group = node_group
    
    # 刷新视图
    bpy.context.view_layer.update()

# 适用于 3D 打印的常用几何节点：
# GeometryNodeMeshBoolean — 非破坏性布尔运算
# GeometryNodeTransform — 精确位置控制
# GeometryNodeConvexHull — 支撑结构生成
# GeometryNodeSubdivisionSurface — 平滑表面
```

### 3. Trimesh 集成 — 质量分析 + 修复

Blender 建完模 → Trimesh 做打印前质检和修复：

```python
import trimesh
import numpy as np

def blender_to_trimesh(obj):
    """Blender mesh → Trimesh 对象"""
    mesh = obj.data
    vertices = np.zeros((len(mesh.vertices), 3))
    mesh.vertices.foreach_get("co", vertices.ravel())
    faces = np.zeros((len(mesh.polygons), 3), dtype=int)
    mesh.polygons.foreach_get("vertices", faces.ravel())
    return trimesh.Trimesh(vertices=vertices, faces=faces)

def analyze_for_printing(obj):
    """打印前用 Trimesh 做全面质检"""
    tm = blender_to_trimesh(obj)
    return {
        'volume': tm.volume,        # mm³
        'surface_area': tm.area,    # mm²
        'watertight': tm.is_watertight,
        'bounds': tm.extents,       # [X, Y, Z] mm
        'faces': len(tm.faces),
        'euler': tm.euler_number,   # 2 = 流型
    }

# 修复流水线
def repair_mesh(obj):
    """Blender → Trimesh 修复 → 回写 Blender"""
    tm = blender_to_trimesh(obj)
    
    # Trimesh 自动修复
    tm.remove_degenerate_faces()
    tm.fill_holes()
    tm.update_faces(tm.nondegenerate)
    trimesh.repair.fix_winding(tm)
    
    # 导出临时 STL 后重新导入 Blender
    tm.export('/tmp/repaired.stl')
    bpy.ops.import_mesh.stl(filepath='/tmp/repaired.stl')
    return bpy.context.object
```

## 🛠️ 大 STL 水密性修复工作流 — Blender edit-mode 手动修复

**场景**: 用户发来的 STL 或你建模导出的 STL 有边界边（非水密），trimesh 自动修复失败（`fill_holes()` 返回 False），需要 Blender 手动修复。

**经验来源**: 50 万面 FFAR1 武器模型，2604 条边界边，trimesh 自动修复全部无效，Blender edit-mode 修复成功。

### 修复前诊断

```bash
# 快速检测水密+边界边数
python3 -c "
import trimesh, sys
m = trimesh.load(sys.argv[1])
euler = len(m.vertices) + len(m.faces) - m.edges_unique.shape[0]
boundary = len([e for e in m.edges_unique if e in m.edges_sl]
                if hasattr(m, 'edges_sl') else [])
print(f'水密: {m.is_watertight}')
print(f'边界边: {m.edges_unique.shape[0] - len(m.edges_sl) if hasattr(m, \"edges_sl\") else \"N/A\"}')
print(f'欧拉数: {euler} (2=流形)')
print(f'非流形边: {len([e for e in m.edges_unique if m.face_adjacency[e]]) if hasattr(m, \"face_adjacency\") else \"N/A\"} ')
" model.stl
```

### 修复阈值判断

| 边界边数 | 策略 | 预期 |
|---------|------|------|
| < 50 条 | trimesh `fill_holes()` 可能成功 | 10 秒完成，✅ |
| 50-500 条 | 尝试 Blender 自动补洞 + remove doubles | 5 分钟，⚠️ 需人工核查 |
| > 500 条 | **必须用 Blender edit-mode 手动修复**，trimesh 对大洞无效 | 参见下方流程，⚠️ 60%+ 可成功 |

### Blender edit-mode 修复流程（已验证于 50 万面 STL）

```python
import bpy, bmesh

def repair_watertight_edit_mode(input_stl, output_stl):
    \"\"\"
    使用 Blender edit-mode 修复大 STL 的水密性。
    原理：select_non_manifold → 删除边界边所在的面 → remove_doubles → fill_holes
    不需要 modifier（避免 headless 下 modifier_apply 静默失败）
    \"\"\"
    # 1. 导入
    bpy.ops.wm.stl_import(filepath=input_stl)
    obj = bpy.context.object
    me = obj.data
    
    # 2. 进入 edit-mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    # 3. 选中非流形顶点并删除其所在面
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
    # 扩展选区到关联面
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_linked()
    
    # 4. 删除选中面
    bpy.ops.mesh.delete(type='FACE')
    
    # 5. 回到顶点模式，合并重叠顶点
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    
    # 6. 补洞
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill_holes(sides=64)  # 64 边限制足够
    
    # 7. 回到 object 模式
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 8. 验证
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    non_manifold = [e for e in bm.edges if not e.is_manifold]
    bm.free()
    print(f"Non-manifold after fix: {len(non_manifold)}")
    
    # 9. 导出
    bpy.ops.wm.stl_export(filepath=output_stl)
    return len(non_manifold) == 0

# 使用
success = repair_watertight_edit_mode(
    '/path/to/bambu_fixed.stl',
    '/path/to/watertight_final.stl'
)
print(f"水密修复{'成功' if success else '失败，残留非流形边'}")
```

### 修复后验证

```python
import trimesh, sys
m = trimesh.load(sys.argv[1])
print(f"✅ 水密: {m.is_watertight}")
print(f"✅ 面数: {len(m.faces):,}")
print(f"✅ 体积: {m.volume:.1f} mm³")

bound_edges = m.boundary_edges()
print(f"边界边: {len(bound_edges)}" + (" ✅ 无水密问题" if len(bound_edges)==0 else " ⚠️"))

# 如果边界边>0但非流形边=0：trimesh 和 Blender 判断有差异，通常可打印
```

### ⚠️ trimesh vs Blender 水密性判断差异

**观测事实（50 万面 STL 实测，2026-06-08）：**

| 工具 | 修复前 | 修复后 | 备注 |
|------|-------|-------|------|
| Blender select_non_manifold | 17 条非流形边 | 0 条 | ✅ |
| trimesh `is_watertight` | False | False | ❌ 仍报 False |
| trimesh `boundary_edges()` | 2604 条 | 0 条 | ✅ |
| trimesh 多余非流形边（4-face shared） | 5 条 | 5 条 | ⚠️ 微小重叠面 |

**结论：当 `blender非流形=0` 且 `trimesh边界边=0` 时，模型对 Bambu Studio/Cura 切片完全安全。** trimesh 报告的额外非流形边（4-face 共享边，重叠面厚度 < 0.001mm）不影响打印，切片软件会自动处理。**不要因此继续迭代修复**——会陷入无限循环。

**经验教训（50万面 STL，2604 条边界边实测）：**
- `fill_holes()` 返回 False → trimesh 自动修复能力远弱于宣传，对小洞（<100 边界边）有效，对大面积破面无效
- `convex_hull()` 缺 scipy 直接抛异常——这不是可选依赖，对某些修复路径是必须的
- **真正的替代方案：** Cura / Bambu Studio 的自动修复（GUI），或 Blender 手动补面

### 4. CadQuery 集成 — 精确参数化零件

对需要精确尺寸的功能性零件（卡扣、齿轮、连接件），先用 CadQuery 建好，再导入 Blender 做美学处理和渲染：

```python
import cadquery as cq

# 在 CadQuery 中设计精确零件
result = (cq.Workplane("XY")
          .box(10, 10, 5)
          .faces(">Z").circle(3).cutThruAll())

# 导出 STL 后导入 Blender
result.exportStl('/tmp/cq_part.stl')
bpy.ops.import_mesh.stl(filepath='/tmp/cq_part.stl')

# 或者导出 STEP 用 Blender STEP 导入器保留精度
result.exportStep('/tmp/cq_part.step')
bpy.ops.wm.step_import(filepath='/tmp/cq_part.step')
```

### 5. 性能优化

```python
# 批量操作：关闭撤销以节省内存
bpy.context.preferences.edit.use_global_undo = False

# 避免频繁 update
# WRONG: 每次修改都 update
# RIGHT: 批量操作完一次性 commit

# 用 foreach_set 而不是逐顶点设置
# WRONG:
# for v in mesh.vertices: v.co = (x, y, z)
# RIGHT:
# coords = np.array([...])  # 批量生成
# mesh.vertices.foreach_set("co", coords.ravel())
```

---

## 3D 打印关节设计方法论

### 核心设计原则

| 原则 | 说明 | 参数 |
|------|------|------|
| **间隙配合** | 两个活动部件之间留间隙 | 0.2-0.4mm（FDM） |
| **倒角/圆角** | 关节接口处加 0.3-0.5mm 倒角减少摩擦 | 0.3-0.5mm |
| **层线方向** | 设计时让层线不垂直于关节轴 | 关节轴平行于打印方向 |
| **免支撑** | 避免 >45° 悬垂设计 | 分体打印，插接组装 |
| **组装方向** | 部件只能沿预期方向移动 | 单一轴向约束 |

### 球关节

```python
import bpy
import math

def create_ball_joint(radius=5, stem_length=10, stem_radius=2, tolerance=0.3):
    """创建球关节对（公头+母头）"""
    # 公头（球 + 杆）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(0, 0, 0))
    ball = bpy.context.object
    ball.name = "Joint_Ball"
    
    # 切平底部用于连接杆
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, 0, -radius * 0.3),
        plane_no=(0, 0, 1),
        clear_inner=True
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 加杆
    bpy.ops.mesh.primitive_cylinder_add(
        radius=stem_radius, depth=stem_length,
        location=(0, 0, -radius * 0.3 - stem_length/2)
    )
    stem = bpy.context.object
    stem.name = "Ball_Stem"
    
    # 合并
    bpy.ops.object.select_all(action='DESELECT')
    ball.select_set(True)
    stem.select_set(True)
    bpy.context.view_layer.objects.active = ball
    bpy.ops.object.join()
    
    # 母头（插座）— 比球体大 tolerance
    socket_radius = radius + tolerance
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=socket_radius,
        location=(0, 0, -radius * 2 - stem_length)
    )
    socket = bpy.context.object
    socket.name = "Joint_Socket"
    
    # 切开顶部留开口
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, 0, -radius * 2 - stem_length + socket_radius * 0.6),
        plane_no=(0, 0, 1),
        clear_outer=True
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 布尔运算挖空
    ball_copy = ball.copy()
    ball_copy.data = ball.data.copy()
    bpy.context.collection.objects.link(ball_copy)
    ball_copy.location.z += radius * 2 + stem_length
    
    bool_mod = socket.modifiers.new(name="Cavity", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = ball_copy
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
    return ball, socket
```

### 铰链关节

```python
def create_hinge_joint(pin_radius=2, knuckle_width=5, clearance=0.3):
    """创建铰链关节（公头叶片+母头叶片+销轴）"""
    # 公头叶片（单叶片）
    bpy.ops.mesh.primitive_cube_add(
        size=1, location=(0, 0, 0)
    )
    blade = bpy.context.object
    blade.scale = (knuckle_width, 3, pin_radius * 2)
    bpy.ops.object.transform_apply(scale=True)
    
    # 公头销孔
    bpy.ops.mesh.primitive_cylinder_add(
        radius=pin_radius + clearance,
        depth=knuckle_width + 1,
        location=(0, 1.5, 0),
        rotation=(math.radians(90), 0, 0)
    )
    hole_cutter = bpy.context.object
    
    bool_mod = blade.modifiers.new(name="Hole", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = hole_cutter
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
    return blade
```

### 拆分打印策略

```python
def split_for_printing(obj, cut_axis='Z', cut_height=0):
    """沿平面拆分模型为多部件打印"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    plane_no = (0, 0, 1)
    if cut_axis == 'X': plane_no = (1, 0, 0)
    elif cut_axis == 'Y': plane_no = (0, 1, 0)
    
    bpy.ops.mesh.bisect(
        plane_co=(0, 0, cut_height),
        plane_no=plane_no,
        clear_inner=False,
        clear_outer=False
    )
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
```

---

## EEVEE 渲染优化（headless 模式）

### 🚨 EEVEE World Background Color Rendering Bug (M4 iGPU)

**OBSERVED FACT**: EEVEE world background node color does NOT render at the value you set.

| Set in node | Actual pixel output | |
|------------|-------------------|-|
| 0.95 gray (RGB 242,242,242) | ~0.74-0.77 (RGB 189-196) | Light background renders as medium gray |
| 0.15 dark gray | ~0.08-0.12 | Dark renders even darker |

**Impact**: If you set material Base Color to 0.5 (to contrast against 0.95 background), the actual contrast in rendered image is only ~5%, making the model nearly invisible against background. The user will see "一片灰色" with no distinguishable object.

**Fix**: Always use a **physical white plane** (not world background) as the backdrop:
```python
# Instead of relying on world bg:
# World node (unreliable on M4):
# bg_node.inputs['Color'].default_value = (0.95, 0.95, 0.95, 1.0)

# Use a physical plane instead:
bpy.ops.mesh.primitive_plane_add(size=500, location=(0, 0, -1))
plane = bpy.context.object
plane.name = "Background"
mat = bpy.data.materials.new("BgMat")
mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
plane.data.materials.append(mat)
```
And set material Base Color to at least 0.15-0.3 (dark gray) for the model, not 0.5.

### 🚨 Fail-Fast Rule: EEVEE renders turn monochrome → stop immediately

**OBSERVED BEHAVIOR (3 separate render attempts in one session):**

When rendering a weapon model (140mm × 18mm × 46mm) with Blender EEVEE headless on Mac Mini M4:

| Attempt | Material | Background | Lights | Result |
|---------|----------|-----------|--------|--------|
| 1 | Gray matte 0.75 | World bg 0.95 | 3× Area (600/300/200) | Object blends into bg (< 5px difference), user: "看不到全貌" |
| 2 | Dark gray 0.15 + White plane 500×500 | World bg 0.95 | 3× Area (1500/500/300) | 100% uniform dark render (0% background pixels detected) |
| 3 | Dark gray 0.15 + White plane | World bg 0.95 | 3× Area (1500/500/300) + PERSP camera | Same: 100% uniform dark |

**Root cause**: EEVEE headless on M4 integrated GPU has unpredictable rendering behavior with Area lights. The white background plane (500×500) was not receiving enough light to appear white. The actual pixel values ranged only 184-207 across the entire image — barely 23 levels of dynamic range in an 8-bit image.

**Fail-Fast Rule（必须在渲染失败一次后执行）:**

```python
# After first render attempt that looks bad to user:
from PIL import Image
import numpy as np
img = Image.open('render.png')
arr = np.array(img.convert('L'))
dynamic_range = arr.max() - arr.min()
print(f"Dynamic range: {dynamic_range}")
if dynamic_range < 50:
    print("FAIL-FAST: EEVEE render is monochrome. Skip EEVEE iterations.")
    print("→ Switch to line-art preview (stl_2d_preview.py)")
    # Do NOT adjust: materials, camera position, background color, lighting
    # The render engine itself is the bottleneck
```

**Do NOT enter a render tuning loop** (adjusting camera → contrast → materials → lights → re-render → user still can't see → repeat). This wastes 3+ cycles with zero improvement. Instead:
1. Immediately generate `stl_2d_preview.py` line-art (front/side/iso views)
2. Send line-art to user for structure verification
3. If user insists on color render, use Cycles (not EEVEE) — but warn it takes 30-60s per frame
4. Accept that M4 iGPU headless EEVEE cannot produce high-contrast renders for long/thin objects

#### 🚨 Blender EEVEE 渲染在 Mac Mini M4 上的局限性

⚠️ **2026-06-09 更新：Blender 5.1.2 完全不可用**

在 Blender 5.1.2 (hash ec6e62d40fa9, built 2026-05-19) 上，EEVEE 的 `--background` 渲染输出 **#000000 纯黑帧**（1920×1080）。所有场景元素（灯光、材质、相机、环境色）配置正确，渲染日志无错误，但输出文件为空帧。这比之前的"灰度缺陷"更严重——是完全不可用。

**硬规定**：默认使用 `scripts/stl_2d_preview.py`（PIL + 面法线着色 + 三点光源）进行任何视觉预览。仅在用户明确要求时尝试 EEVEE，且渲染后必须自动检测（if std < 50 → 回退 PIL）。

**观测事实（经过本用户环境多次验证）：**

Blender headless EEVEE 在 Mac Mini M4 (16GB, 无独显) 上渲染 3D 模型时，输出图像存在**一致性缺陷**：

| 问题 | 表现 | 根本原因 |
|------|------|---------|
| 颜色不准 | 深色材质渲染为浅灰色 | EEVEE 在 headless 下材质采样偏差 |
| 光照扁平 | 多盏 Area 光源看不出立体感 | 软光在无独显 GPU 下衰减异常 |
| 对比度低 | 物体与背景差异小 | 整个渲染画面趋向均匀灰色 |
| 构图难控制 | ORTHO 长细物体（140mm×18mm）100% 填满画面 | 相机自动对焦算法未考虑纵横比悬殊的物体 |

**策略：对于所有需要用户视觉审核的模型，优先使用 2D 线框/三角面预览，Blender EEVEE 仅作为"补充彩色参考"，不作为主要审核手段。**

```python
# 决策矩阵：选择预览方式
# 1. 形状/结构审核 → stl_2d_preview.py (2D 线框投影) — 可靠、快、不依赖 GPU
# 2. 尺寸/比例审核 → trimesh 或 numpy-stl 分析 bounding box
# 3. 彩色/质感展示 → Blender EEVEE（但告知用户可能颜色不准）
# 4. 最终用户审核 → 直接发 STL 文件给用户在本地查看
```

### 🚨 新增: 模型物理尺寸 < 50mm 时的相机策略

**场景**: 用户发来的 STL 只有几厘米甚至几毫米（如 TEMI 模型仅 8mm 宽 × 100mm 长 × 28mm 高），Blender 渲染全黑。

**问题**: Blender EEVEE 渲染时，默认相机距离可能设置为 `max_dim * 1.5`，当模型很小（如 8mm 宽）时，相机距离仅 0.15m，但 Blender 的 STL 导入坐标系单位为米，200mm 以上的相机距离 → 模型在画面中变成米粒大 → 背景白 → 用户看到"全黑"或"全白"。

**诊断脚本（渲染前必须执行）**:
```python
import numpy as np
fname = 'your_model.stl'
with open(fname, 'rb') as f:
    data = f.read()
num_tris = int.from_bytes(data[80:84], 'little')
verts = []
for i in range(num_tris):
    offset = 84 + i * 50
    for j in range(3):
        v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
        verts.append(v)
verts = np.array(verts)
ranges = [verts[:,i].max()-verts[:,i].min() for i in range(3)]
print(f'尺寸: {ranges[0]:.1f}x{ranges[1]:.1f}x{ranges[2]:.1f}mm')
print(f'质心Z: {verts[:,2].mean():.1f}')
```

**相机距离公式（按模型大小分档）:**

| 模型最大尺寸 | 相机距离 | 镜头焦距 | 适用场景 |
|-------------|---------|---------|---------|
| 5-50mm | `max_dim * 2.5` | 50mm | 小零件、微缩模型 |
| 50-200mm | `max_dim * 1.5` | 50mm | 标准打印件 |
| 200mm+ | `max_dim * 1.2` | 35mm | 大件（避免裁切） |

```python
# 正确的相机设置
max_dim = max(obj.dimensions.x, obj.dimensions.y, obj.dimensions.z)
if max_dim < 0.05:        # < 50mm
    cam_dist = max_dim * 2.5
    lens = 50
elif max_dim < 0.20:      # 50-200mm
    cam_dist = max_dim * 1.5
    lens = 50
else:                      # > 200mm
    cam_dist = max_dim * 1.2
    lens = 35

cam.data.lens = lens
cam.location = (cam_dist * 0.4, -cam_dist * 0.8, cam_dist * 0.3)
```

**渲染前的自我验证（发送用户前必须做）**:
```python
from PIL import Image
import numpy as np
img = Image.open('render.png')
arr = np.array(img.convert('L'))
print(f'渲染亮度均值: {arr.mean():.1f}')
assert arr.mean() > 30, "❌ 渲染很可能全黑，调整相机/灯光"
```

> **这是本技能中最容易出现"用户说看不到图"的部分。以下规则经过了 OPPO Find N5 手机壳 8 次迭代的教训验证，必须遵守。关键教训：渲染失败时先查 STL 文件本身，而非盲目切换渲染引擎。**

用户通过飞书/Telegram 等 IM 平台看到渲染图。一条"全黑"或"看不到"的反馈 = 渲染失败。

### 全黑诊断协议（盲修前必须执行）

**第 0 步：先检查 STL 文件的物理尺寸和顶点范围**

> ❗ 这是最常见也最隐蔽的原因：STL 模型本身尺寸/位置错误，那么无论用什么引擎、多少灯光、什么背景颜色，渲染都不可见。

```bash
# 检查 STL 顶点范围 — 验证模型的物理尺寸是否合理
python3 -c "
import numpy as np
for fname in ['model_left.stl', 'model_right.stl']:
    with open(fname, 'rb') as f:
        data = f.read()
    num_tris = int.from_bytes(data[80:84], 'little')
    verts = []
    for i in range(num_tris):
        offset = 84 + i * 50
        for j in range(3):
            v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
            verts.append(v)
    verts = np.array(verts)
    print(f'{fname}: {num_tris} tris')
    print(f'  X: {verts[:,0].min():.1f} ~ {verts[:,0].max():.1f}')
    print(f'  Y: {verts[:,1].min():.1f} ~ {verts[:,1].max():.1f}')
    print(f'  Z: {verts[:,2].min():.1f} ~ {verts[:,2].max():.1f}')
    # 诊断
    ranges = [verts[:,i].max()-verts[:,i].min() for i in range(3)]
    for i, axis in enumerate(['X','Y','Z']):
        if ranges[i] < 1.0:
            print(f'  ⚠️  {axis} 方向仅 {ranges[i]:.2f}mm —— STL 被严重压扁或位置错误！')
"
```

**诊断规则（发完 STL 后立即执行，不等用户反馈）：**

| STL 顶点特征 | 诊断 | 修复 |
|-------------|------|------|
| 某轴范围 < 1mm | 生成错误 → 模型被压成薄片 | 检查建模脚本的尺寸/缩放参数 |
| 模型质心在 Z<0 | 相机默认朝 Z>0 拍 → 拍不到 | 平移模型至 Z>0 |
| 三角面数 < 50 | 生成可能失败 | 检查几何体函数是否正确生成面 |
| 各轴范围合理（如 > 20mm） | STL 本身 OK → 问题在渲染设置 | 进入第 1 步 |

**第 1 步：接收用户反馈"全黑"后，先检查渲染图像素**

```python
from PIL import Image
import numpy as np
img = Image.open('render.png').convert('RGB')
arr = np.array(img)
print(f"Mean: {arr.mean():.1f}, Min: {arr.min()}, Max: {arr.max()}")

# 分区域检查
h, w = arr.shape[:2]
for label, region in [
    ('center', arr[h//4:3*h//4, w//4:3*w//4]),
    ('top-left', arr[:h//3, :w//3]),
]:
    print(f"  {label}: mean={region.mean():.1f}")
```

**像素诊断规则：**
| 特征 | 诊断 | 修复 |
|------|------|------|
| 全图均匀 (max-min<3) | 画面完全空 → STL 不在相机视野或渲染引擎未渲染物体 | 检查相机位置/STL 坐标/Blender 物体选择 |
| 有差异但 max<80 | 物体在画面中但极暗 | 加光源 + 浅色背景 + 亮色材质 |
| 均值>200 | 渲染基本正常，用户可能没注意到图片 | 确认图片已发送且文件非空 |
| 均值 30-80 | 有内容但很暗，可能 IM 压缩导致 | 降低分辨率到 800×600, JPEG Q85 |

**第 2 步：2D Pillow 预览（Blender 渲染失败时的应急方案）**

当 Blender EEVEE/Cycles/Workbench 均无法正确渲染材质颜色时（headless 模式已知有此问题），用 Python PIL 生成 2D 线框投影预览：

```python
from PIL import Image, ImageDraw
import numpy as np, math

def project_2d(verts, rot_x=0, rot_y=0, rot_z=0):
    \"\"\"3D 顶点 → 2D 透视投影\"\"\"
    cx, cy = 600, 400
    scale = 3.0  # 缩放因子，根据模型大小调整
    rx, ry, rz = map(math.radians, [rot_x, rot_y, rot_z])
    
    # 旋转矩阵
    def rotate(v):
        x, y, z = v
        # Y 旋转
        x, z = x*math.cos(ry)+z*math.sin(ry), -x*math.sin(ry)+z*math.cos(ry)
        # X 旋转
        y, z = y*math.cos(rx)-z*math.sin(rx), y*math.sin(rx)+z*math.cos(rx)
        # Z 旋转 (俯视)
        x, y = x*math.cos(rz)-y*math.sin(rz), x*math.sin(rz)+y*math.cos(rz)
        return x, y, z
    
    projected = []
    for v in verts:
        x, y, z = rotate(v)
        projected.append((cx + x*scale, cy - z*scale))  # Y→屏幕深度, Z→屏幕Y
    return projected

# 加载 STL 并渲染 2D 预览
def stl_to_2d_preview(stl_path, output_path, rot_x=0, rot_y=30):
    with open(stl_path, 'rb') as f:
        data = f.read()
    num_tris = int.from_bytes(data[80:84], 'little')
    verts = []
    for i in range(num_tris):
        offset = 84 + i * 50
        tri_verts = []
        for j in range(3):
            v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
            tri_verts.append(v)
        verts.append(tri_verts)
    
    img = Image.new('RGB', (1200, 800), 'white')
    draw = ImageDraw.Draw(img)
    
    for tri in verts:
        pts = project_2d(tri, rot_x, rot_y)
        draw.polygon(pts, fill='lightblue', outline='darkblue', width=1)
    
    img.save(output_path)
```

### 渲染核心策略

```python
def setup_visible_render(scene):
    """配置 EEVEE 渲染，确保模型对用户可见"""
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    # ⚠️ 不要用 film_transparent=True! 透明底 + 小模型 = 全黑
    scene.render.film_transparent = False  # 使用场景背景色
    
    # 设置浅色背景
    world = scene.world
    if not world.use_nodes:
        world.use_nodes = True
    bg_node = world.node_tree.nodes.get('Background')
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.95, 0.95, 0.95, 1.0)
        bg_node.inputs['Strength'].default_value = 1.0
    
    # EEVEE 优化
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_gtao = True
    scene.eevee.use_volumetric = False
    
    return scene

def setup_lights(scene):
    """添加三光源照明：主光+补光+背光，确保模型不暗"""
    # 清除默认灯光
    for obj in list(scene.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj)
    
    # 主光 - 暖色，右前上方
    bpy.ops.object.light_add(type='AREA', location=(10, -8, 12))
    main_light = bpy.context.object
    main_light.data.energy = 500
    main_light.data.color = (1.0, 0.9, 0.7)  # 暖色
    
    # 补光 - 冷色，左后下方
    bpy.ops.object.light_add(type='AREA', location=(-8, 8, 5))
    fill_light = bpy.context.object
    fill_light.data.energy = 300
    fill_light.data.color = (0.7, 0.8, 1.0)  # 冷色
    
    # 背光 - 轮廓光
    bpy.ops.object.light_add(type='SUN', location=(0, 10, 5))
    back_light = bpy.context.object
    back_light.data.energy = 2.0

def assign_bright_material(obj, color=(0.8, 0.2, 0.2, 1.0)):
    """给对象赋予亮色材质，使其在浅背景上清晰可见"""
    mat = bpy.data.materials.new(f"Mat_{obj.name}")
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get('Principled BSDF')
    if principled:
        principled.inputs['Base Color'].default_value = color
        principled.inputs['Roughness'].default_value = 0.4
        principled.inputs['Metallic'].default_value = 0.0
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
```

**第 2 层（用户反馈"全黑"后的修复策略）：**

如果用户说 "看不到" / "全黑的" / "什么也没有"，不要重新建模或猜测尺寸——问题出在渲染，不是模型。按以下顺序排查：

```python
# 1. 检查渲染图是否真的全黑
from PIL import Image
import numpy as np
img = Image.open('render_output.jpg')
arr = np.array(img.convert('L'))
print(f"Mean brightness: {arr.mean():.1f}")  # < 30 = 真的全黑; > 30 = 可见但用户可能没注意到

# 2. 修复步骤（依优先级）
#    a) 禁用 film_transparent → 设置浅色背景
#    b) 加多光源（至少三盏）
#    c) 赋予亮色材质（红、蓝、橙等高饱和度颜色）
#    d) 拉近相机 → 让模型占据画面 60%+
#    e) 降低分辨率到 800×600 或更小（飞书/Telegram 对大图压缩可能导致变黑）
#    f) 输出 JPEG 而非 PNG
#    g) 发送前检查文件大小（< 200KB 最佳）

# 3. 快速修复模板
def render_visible_fix(scene, obj, output_path, scale_distance=1.0):
    """修复版本：强行缩放到可见"""
    # 拉近相机
    camera = scene.camera
    bounds = obj.dimensions
    max_dim = max(bounds.x, bounds.y, bounds.z)
    camera.location = (max_dim * 2, -max_dim * 2, max_dim * 1.5)
    camera.data.lens = 35  # 标准焦距，不扭曲
    
    # 确保世界背景浅色
    scene.render.film_transparent = False
    bg = scene.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (0.92, 0.92, 0.92, 1.0)
    
    # 降低分辨率保证传输
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.filepath = output_path
    
    bpy.ops.render.render(write_still=True)
```

### 快速多角度渲染

```python
import bpy
import math

def setup_fast_render(scene):
    """配置 EEVEE 为最快渲染模式"""
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    scene.render.film_transparent = False  # 浅色背景，不要透明
    
    # 设置浅色世界背景
    world = scene.world
    if not world.use_nodes:
        world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.92, 0.92, 0.92, 1.0)
    
    # EEVEE 优化（关掉不需要的效果）
    scene.eevee.taa_render_samples = 16   # 低 = 更快
    scene.eevee.use_gtao = True           # 保持一定阴影深度感
    scene.eevee.use_volumetric = False    # 关体积光
    
    return scene

def render_views(output_prefix, views):
    """批量渲染多角度预览图"""
    scene = setup_fast_render(bpy.context.scene)
    
    for label, loc, rot in views:
        # 创建临时相机
        cam_data = bpy.data.cameras.new(f"Cam_{label}")
        cam_obj = bpy.data.objects.new(f"CamObj_{label}", cam_data)
        bpy.context.collection.objects.link(cam_obj)
        cam_obj.location = loc
        cam_obj.rotation_euler = rot
        
        scene.camera = cam_obj
        scene.render.filepath = f"{output_prefix}_{label}.jpg"
        bpy.ops.render.render(write_still=True)
        
        # 清理
        bpy.data.objects.remove(cam_obj)
        bpy.data.cameras.remove(cam_data)

# 常用视角组合
views = [
    ("front",     (0, -6, 3), (math.radians(70), 0, 0)),
    ("isometric", (5, -5, 5), (math.radians(60), 0, math.radians(45))),
    ("side",      (6, 0, 3),  (math.radians(70), 0, math.radians(90))),
    ("top",       (0, 0, 8),  (math.radians(0), 0, 0)),
]
```

### 性能数据（Mac Mini M4 16GB）

| 操作 | 耗时 |
|------|------|
| Blender headless 启动 | 3-4s |
| EEVEE 1200×800 单视角 | 1-3s |
| EEVEE 1920×1080 高质量 | 4-6s |
| 批量 4 视角渲染 | 8-12s |
| STL 导出（小部件<2K面） | ~4ms |
| STL 导出（大部件~50K面） | ~16ms |

---

## 推荐工作流模板

对于一个完整的 3D 打印项目，推荐的脚本组织：

```
项目目录/
├── model_gen.py          # 主建模脚本（Blender bpy）
├── model_repair.py       # Trimesh 质检+修复
├── render_views.py       # 多角度渲染预览
└── output/               # 输出目录
    ├── part_*.stl        # 分体 STL
    ├── assembled.stl     # 组装参考
    └── view_*.jpg        # 预览图
```

### 完整的端到端流水线

```bash
# 1. 建模 + 导出 STL
blender --background --python model_gen.py

# 2. 质检
python3 -c "
import trimesh
m = trimesh.load('output/part_00.stl')
print(f'水密: {m.is_watertight}, 体积: {m.volume:.1f}mm³, 尺寸: {m.extents}')
"

# 3. 渲染预览
blender --background --python render_views.py

# 4. 发送给用户
```

这与 `python-3d-tools` 技能、`bambu-lab-tips` 技能互补使用。

## 超大 STL 快速预览协议（跳过 Blender，>5万面时使用）

当 STL 文件超过 5 万面（约 2.5MB+），Blender 导入+渲染耗时 >30 秒，且容易因为模型尺寸/位置问题导致全黑。**此时应先用 Python 直接读二进制 STL 画 2D 线框预览，确认模型形状正确后，再用 Blender 做精细渲染。**

```python
from PIL import Image, ImageDraw
import numpy as np, math

def stl_to_2d_preview(stl_path, output_path, scale=2.0, sample_ratio=1.0):
    """
    二进制 STL → 2D 线框预览（不依赖 Blender）
    sample_ratio: 对超大文件(>100万面)可设 0.1 采样10%加速
    """
    with open(stl_path, 'rb') as f:
        data = f.read()
    num_tris = int.from_bytes(data[80:84], 'little')
    
    # 对超大文件随机采样
    if sample_ratio < 1.0:
        import random
        rng = random.Random(42)
        sample_indices = set(rng.sample(range(num_tris), int(num_tris * sample_ratio)))
    else:
        sample_indices = None
    
    # 计算质心和范围用于自动缩放
    all_verts = []
    for i in range(min(5000, num_tris)):
        offset = 84 + i * 50
        for j in range(3):
            v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
            all_verts.append(v)
    all_verts = np.array(all_verts)
    center = all_verts.mean(axis=0)
    max_range = max(all_verts.ptp(axis=0))
    auto_scale = 800 / max_range if max_range > 0 else 1.0
    
    img_size = 1200
    img = Image.new('RGB', (img_size, img_size), 'white')
    draw = ImageDraw.Draw(img)
    
    tri_count = 0
    for i in range(num_tris):
        if sample_indices is not None and i not in sample_indices:
            continue
        offset = 84 + i * 50
        tri_pts = []
        for j in range(3):
            v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
            # 正交投影到 XY 平面，居中
            px = img_size/2 + (v[0] - center[0]) * auto_scale * scale
            py = img_size/2 + (v[2] - center[2]) * auto_scale * scale  # Z 朝上
            tri_pts.append((px, py))
        draw.polygon(tri_pts, fill='lightblue', outline='darkblue', width=1)
        tri_count += 1
    
    # 角标信息
    info = f"Tris: {tri_count}/{num_tris} | Size: {max_range*auto_scale*scale:.0f}px"
    draw.text((10, 10), info, fill='black')
    img.save(output_path)
    print(f"2D preview saved: {output_path}")
    return True
```

**决策矩阵：用哪个预览方案：**

| 文件大小 | 三角面数 | 预览方案 | 耗时 |
|---------|---------|---------|------|
| < 2MB | < 5 万 | Blender EEVEE 直接渲染 | ~5s |
| 2-10MB | 5-20 万 | 先 2D 线框确认形状，再 Blender 渲染 | ~15s |
| > 10MB | > 20 万 | 仅 2D 线框（采样 10%），告知用户文件过大 | < 5s |

### 长条/细长物体的 ORTHO 侧视图构图策略

> **核心教训来自 FFAR1 武器模型（140mm 长 × 18mm 宽 × 46mm 高）。** ORTHO 相机从侧面拍时，物体在画面中仅占 13.8%，用户反馈："看不到全貌"。

**问题根源：** 武器侧对着 ORTHO 相机时，水平方向（X 轴）看的是物体宽度方向（18mm），垂直方向（Z 轴）看的是高度（46mm），而深度方向（Y 轴、长轴 140mm）被压扁不可见 → 画面 86% 是背景。

**渲染前必须执行的填充率检查：**

```python
from PIL import Image
import numpy as np

def check_render_fill(render_path, bg_color_rgb=(242, 242, 255), tolerance=30):
    """检查渲染图中物体占画面的百分比"""
    img = Image.open(render_path).convert('RGB')
    arr = np.array(img)
    
    # 背景像素检测：所有通道都在 bg_color ± tolerance 范围内
    bg_r, bg_g, bg_b = bg_color_rgb
    is_bg = (
        (np.abs(arr[:,:,0].astype(int) - bg_r) < tolerance) &
        (np.abs(arr[:,:,1].astype(int) - bg_g) < tolerance) &
        (np.abs(arr[:,:,2].astype(int) - bg_b) < tolerance)
    )
    
    object_pixels = (~is_bg).sum()
    total_pixels = arr.shape[0] * arr.shape[1]
    fill_ratio = object_pixels / total_pixels * 100
    
    print(f"Object fills {fill_ratio:.1f}% of frame")
    if fill_ratio < 25:
        print(f"⚠️ 物体仅占画面 {fill_ratio:.1f}% 以下，用户会反馈"看不到全貌"")
        print(f"  → 建议缩小 ORTHO scale 或拉近相机")
    elif fill_ratio > 90:
        print(f"⚠️ 物体几乎占满画面 ({fill_ratio:.1f}%)，用户看不到整体轮廓")
        print(f"  → 建议扩大 ORTHO scale 或拉远相机")
    else:
        print(f"✅ 填充率合理 ({fill_ratio:.1f}%)")
    return fill_ratio
```

**侧视图 ORTHO scale 自动计算公式：**

```python
# 侧视图的可见尺寸：看哪两个轴？
# 从 Y 负方向看（侧视）：可见 Y×Z 投影（深度 × 高度）
visible_x = obj.dimensions.y  # Y = 深度方向 → 水平轴
visible_z = obj.dimensions.z  # Z = 高度方向 → 垂直轴
longest_visible = max(visible_x, visible_z)

# 目标：让最长可见轴占画面 70%
# ORTHO scale = 半画幅宽度，所以 = 最长可见轴 / 2 / 目标填充率
target_fill = 0.70  # 70%
ortho_scale = (longest_visible / 2) / target_fill  # 约 100mm 对 140mm 长轴

# 对侧面相机，正确的相机位置和旋转：
# 从 Y 负方向看 → 相机在 (0, -distance, z_offset)
camera_distance = longest_visible * 1.5  # 1.5 倍足够，因为 ORTHO 不受距离影响
camera_height = obj.dimensions.z / 2     # 让物体垂直居中
camera.location = (0, -camera_distance, camera_height)
```

**对比：PERSP 和 ORTHO 哪个更适合侧视：**

| 方面 | ORTHO | PERSP |
|------|-------|-------|
| 长条物体 | ❌ 最短轴方向画面浪费严重 | ✅ 透视自然压缩远距离，空间利用好 |
| 用户理解难度 | ❌ 物体看起来扁/怪 | ✅ 模拟人眼，更自然 |
| 推荐度 | 仅用于俯视或正视图 | 侧视和透视图首选 |
| 特别注意 | 侧视时需手动调整 scale | 需确认 lens 焦距足够（lens ≥ 85 避免鱼眼变形） |

## Verification

### 🔬 Mandatory: Quality self-check before sending to user

**User's hard rule:** Before sending any model to the user, you MUST perform a strict self-check comparing reference image(s) against the actual STL. Ask two questions:
1. **是不是一个东西？** — Does the STL match the reference object's category and overall silhouette?
2. **是不是一个档次？** — Does the STL have comparable detail level? (Not expecting game-grade polish, but it should be recognizably the same object with the key parts present.)

**Procedure:**
1. Load at least 2-3 reference images (re-analyze with vision_analyze with specific questions)
2. Build a **part inventory** from the reference: list every visible component (barrel, muzzle device, handguard, receiver, grip, magazine, stock, sights, trigger guard, etc.)
3. Compare STL against the inventory — check for missing parts explicitly
4. Check triangle count: <1000面 = rough shapes only, fine details invisible. Game weapon models need 3000-5000+ faces. **376面以下的STL不可接受用于武器/角色模型** — 这是numpy-stl box组合的典型面数，产生的模型"看不出样子"。
5. Only if the model passes all checks → send to user
6. If it doesn't pass, explain honestly what's missing and offer to improve or ask for more/better reference

**⚠️ 关键：vision_analyze（GLM-4v）在几何参照场景下不可靠**

> **2026-06-09 更新**: 发现 Qwen3-VL-Plus（阿里百炼，¥2.5-5/M tokens）具有明确的"空间感知"能力，应替代 GLM-4v 用于 3D 模型参考分析。详见 `references/qwen3-vl-plus-vision-for-3d.md`。

经过多次验证，GLM-4v 在分析武器/模型截图时会出现**明确幻觉**——即给出的描述不是"模糊"，而是**错误的**：
- 报告中称"没有枪口制退器"——实际参考图中制退器明显可见
- 称"垂直握把"——实际握把有明显倾斜角度
- 称"看不到弹匣"——实际弹匣在侧面明显可见
- 同一张渲染图，GLM先后报告过"没有枪口制退器"、"黑色矩形网格"（实际是浅色背景）

**正确做法：**
1. vision_analyze 只用于**概览型审查**（"这大概是什么类型的东西"），**不能用于获取精确的部件几何数据**（尺寸、角度、位置关系）
2. 部件几何数据来自：B站4K无UI展示视频的截图、官方概念图、纸板手工拆解图——这些都是人类设计师制作的参考，不需要AI解读
3. 建模前，用**人工肉眼**（你自己的推理）从参考图提取部件信息：枪管长度比例、握把角度、弹匣位置、枪托形状
4. 只有当你看到参考图中一个部件**确实有明确轮廓**时，才把它建进模型。GLM说"看不见"不代表真的没有

**When vision_analyze gives vague descriptions** (e.g. "流线型" "复杂几何" with no specific geometry): Do NOT model based on one vague call. Analyze each reference image independently with specific questions about each part. Note which parts have reliable data vs. which are conjectural. If GLM reports a part as "不存在" but your own reasoning from the reference image says it should be there, trust your reasoning — GLM hallucinates absence as often as presence.

After generating STLs (do this BEFORE rendering or sending to user):
After generating STLs (do this BEFORE rendering or sending to user):
> For one-piece boolean UNION models, see `references/one-piece-boolean-union.md` for the dedicated verification procedure including bottom-flatness check and vertex-range analysis.
> For cartoon character models (animals, mascots, action figures), see `references/cartoon-character-modeling.md` for the complete part-inventory checklist and feature-building guide — run the verification script there before sending to the user.
> For weapon/mecha models, see `references/weapon-blender-modeling.md` for tool-selection guidance and Blender 5.x export fix.
For the contour extraction + gaussian smoothing + side-profile extrusion pipeline, see `references/contour-extraction-smoothing-pipeline.md`.
> For headless Blender rendering failure (uniform gray renders), see `references/ffar1-modeling-case-study.md` — the lesson is to skip EEVEE and use `scripts/stl_2d_preview.py` instead.
> For Blender headless modifier failure (SUBSURF/MIRROR apply silently fails), see `references/blender-modifier-headless-pitfall.md` and `references/blender-headless-bmesh-subdivide.md`.
> For editing an existing STL (add features / cut parts / merge), see `references/stl-editing-workflow-case-study.md` and the **STL 编辑工作流** section above.
> For rebuilding from an approved model's render contour (approved silhouette → contour extraction → fresh side-extrusion rebuild → add details), see `references/approved-model-contour-rebuild.md`.
> For user-provided task briefs in numbered checklist format, see `references/user-task-brief-protocol.md`.

After generating STLs (do this BEFORE rendering or sending to user):
1. **Check STL bounding box** — verify all axes have sensible ranges (not < 2mm, not in negative Z):
   ```bash
   python3 -c "
   import numpy as np
   for fname in ['part_a.stl', 'part_b.stl']:
       with open(fname, 'rb') as f:
           data = f.read()
       num_tris = int.from_bytes(data[80:84], 'little')
       verts = []
       for i in range(num_tris):
           offset = 84 + i * 50
           for j in range(3):
               v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
               verts.append(v)
       verts = np.array(verts)
       ranges = [verts[:,i].max()-verts[:,i].min() for i in range(3)]
       ok = 'OK' if min(ranges)>=2.0 and verts[:,2].mean()>0 else 'SUSPICIOUS'
       print(f'{fname}: {num_tris} tris, {ranges[0]:.0f}x{ranges[1]:.0f}x{ranges[2]:.0f}mm [{ok}]')
   "
   ```
2. **Check file sizes** — each part should be non-trivially sized (>1KB)
3. **Preview image** — for Blender models, render with EEVEE: `blender --background --python render_preview.py`
4. **Self-verify the render** — after rendering, check pixel brightness:
   ```bash
   python3 -c "
   from PIL import Image; import numpy as np
   img = Image.open('preview.jpg').convert('L')
   arr = np.array(img)
   print(f'Mean brightness: {arr.mean():.1f}')
   if arr.mean() < 30: print('WARNING: Render may appear all-black to user!')
   "
   ```
5. **Merge tolerance** — check that parts interlock, not intersect (GAP handles this)
6. **Send preview to user** via MEDIA: path before recommending download of STLs. For IM delivery, keep files under 200KB and use JPEG format for photos.

## Pitfalls

### Pitfalls

- **Point-cloud preview limitations for box-composite models**: When using pure numpy-stl (no Blender), the only preview option is 2D point cloud projection via Pillow. AI vision models **cannot recognize weapon/vehicle shapes** from these point cloud images — they see random dots, not a gun shape. The model only looks correct when opened in a 3D viewer (STL file opened in Preview.app, Bambu Studio, etc.). **Always send the raw STL file to the user** (via MEDIA:) alongside the 2D preview, or ask them to open it locally. Do not iterate blindly on visual feedback from point cloud previews — the model is likely fine, the preview is just inadequate.
- **numpy-stl's Mode in binary export**: Must import `from stl import Mode` explicitly, then use `Mode.BINARY` / `Mode.ASCII`. ASCII mode is readable but ~5x larger — only use for debugging.
- **Face winding**: All triangle faces must have outward-pointing normals. Bottom faces (z=z0) and top faces (z=z1) need opposite winding. The `_extrude` helper handles this — don't try to hand-code vertex ordering without it.
- **Decimal precision**: STL is ASCII float text; coordinate drift >0.1mm matters. Use `np.float64` for vertex arrays.
- **Too-few polygon segments**: <12 segments for circles creates visible faceting on curved surfaces. 16-24 is the sweet spot for desktop FDM (which can't resolve finer than 0.1mm anyway).
- **Memory**: Large models (100K+ faces) can stall numpy-stl. Keep primitive resolution modest (lat_steps=20, lon_steps=20 for spheres).
- **Render "all black" syndrome**: Never use `film_transparent=True` + default dark world background — small/medium models become invisible. Always set a light-colored world background (`0.92, 0.92, 0.92`), disable `film_transparent`, add 3+ lights, and assign bright-colored materials. See EEVEE渲染优化 section for the full protocol.
- **Camera framing**: Subdivision-surfaced models are physically larger than base mesh. Rule of thumb: multiply camera distance by 2× from what feels right. A model that fills 30% of the viewport will look tiny to the user on mobile. Target 60%+ fill.
- **Sent image too large**: IM platforms compress big images. Keep renders ≤ 800×600, JPEG quality 85, file under 200KB. Very large PNGs may appear black due to aggressive server-side compression.
- **No "blind trial" rendering**: If user says "all black", **first check STL vertex bounds** to confirm model dimensions and position are sane. The problem could be the STL itself (wrong scale, wrong position, squished axis) — not just render settings. Don't switch render engines 3+ times without first verifying the input geometry. See `references/debug-render-all-black.md` for a case study.
- **numpy-stl merge_meshes = green blob**: Simply merging overlapping numpy-stl meshes with `_merge_meshes()` retains all internal faces, producing a "green blob" that AI vision models cannot recognize. **Character models must use boolean UNION** (Blender or trimesh) to eliminate internal faces. Pure numpy-stl overlap merging is only acceptable for phone cases and other non-organic models where overlapping regions are minimal.
- **Blender boolean UNION + Decimate = detail loss**: Applying a Decimate modifier after boolean UNION destroys small features (eyes, mouth, fingers). A 2943-vertex model decimated to 0.25 becomes 733 vertices — facial features disappear. **Never decimate character models**. Use `bmesh.ops.remove_doubles()` to clean up duplicate vertices instead. SUBSURF at levels=1 produces reasonable file size without decimation.
- **Blender headless modifier apply fails silently** — SUBSURF, MIRROR, BOOLEAN, ARRAY, BEVEL all fail in `--background` mode. See `references/blender-modifier-headless-pitfall.md` for the diagnosis and manual symmetry workaround. For face-count increase without SUBSURF, see `references/blender-headless-bmesh-subdivide.md` for the `bmesh.subdivide_edges` pattern.
- **Vision unavailable protocol**: When `vision_analyze` fails (401/400) or AI vision can't identify a render: (1) check STL vertex bounds first, (2) generate 2D line-art preview with Pillow (no Blender), (3) send raw files to user via MEDIA: for them to see directly.
