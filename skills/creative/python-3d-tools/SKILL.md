---
name: python-3d-tools
description: "Python 程序化 3D 建模工具链 — CadQuery、trimesh、sdf 等库的安装和使用，用于生成/修复/分析 STL 模型"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [3d-printing, python, cad, trimesh, cadquery, stl, mesh]
    related_skills: [3d-printing, bambu-lab-tips]
---

# Python 3D 建模工具链

Python 生态中有多个优秀的程序化 3D 建模库，可生成、修复、分析和转换 STL 文件。本技能整理最实用的工具及其用法。

## 工具概览

| 工具 | 安装 | 用途 | 推荐场景 |
|------|------|------|---------|
| **trimesh** | `pip install trimesh` | STL 加载/分析/修复/布尔运算/水密性检查 | 导出到切片器前的质量检查 |
| **CadQuery** | `pip install cadquery` | 参数化 CAD 建模（类似 OpenSCAD 但用 Python） | 精确尺寸的机械件/功能性零件 |
| **fogleman/sdf** | `pip install sdf` | 数学公式建模（Signed Distance Function） | 有机/算法形状 |
| **meshio** | `pip install meshio` | 格式互转（STL↔OBJ↔STEP↔PLY↔etc） | 格式转换管线 |
| **pygalmesh** | `pip install pygalmesh` | 隐式表面→STL 网格 | 从数学方程生成 3D 形状 |
| **vedo** | `pip install vedo` | 科学可视化 + STL 处理 | 模型可视化、布尔运算 |

## 1. Trimesh — STL 质检必备

### 安装
```bash
pip install trimesh
```

### 加载和检查模型
```python
import trimesh

# 加载
m = trimesh.load('model.stl')

# 基本统计
print(f"顶点: {len(m.vertices)}")
print(f"三角面: {len(m.faces)}")
print(f"体积: {m.volume:.2f} mm³")
print(f"表面积: {m.area:.2f} mm²")

# 水密性检查（打印前必须通过）
print(f"是否水密: {m.is_watertight}")
print(f"是否流型: {m.is_watertight and m.euler_number == 2}")

# 包围盒
print(f"尺寸: {m.extents} mm")  # [X, Y, Z]
```

### 修复模型
```python
# 自动修复（填充孔洞、合并重合顶点）
m.fill_holes()
m.remove_duplicate_faces()
m.remove_unreferenced_vertices()

# 检查法线并翻转
m.fix_normals()

# 简化网格（减少面数以适合打印）
simplified = m.simplify_quadric_decimation(face_count=5000)
simplified.export('simplified.stl')
```

### 布尔运算
```python
# 两个模型合并
a = trimesh.load('part_a.stl')
b = trimesh.load('part_b.stl')

# 布尔联合（Union）
union = a + b

# 布尔差（Difference） — 在 a 中挖掉 b 的形状
diff = a - b

# 布尔交（Intersection）
inter = a.intersection(b)

union.export('combined.stl')
```

### 生成接头/间隙
```python
# 在圆柱接头周围创建间隙
import numpy as np

# 假设 peg 是圆柱，socket 是孔
peg = trimesh.primitives.Cylinder(radius=2.0, height=5.0)
# 留 0.2mm 间隙（每边 0.1mm）
socket = trimesh.primitives.Cylinder(radius=2.2, height=5.1)

# 在 body 上挖 socket
body = trimesh.load('body.stl')
body_with_hole = body - socket
body_with_hole.export('body_final.stl')
```

## 2. CadQuery — 参数化 CAD 建模

### 安装
```bash
pip install cadquery
```

CadQuery 需要 CAD 内核（默认用 OCCT），在 macOS M 系列上开箱可用。

### 基础用法
```python
import cadquery as cq

# 创建一个基础盒子
result = (
    cq.Workplane("XY")
    .box(10, 10, 5)       # 长宽高
    .faces(">Z").hole(3)  # 顶面打孔
    .faces(">X").circle(2).cutThruAll()  # 侧面打穿
)

# 导出 STL
cq.exporters.export(result, 'part.stl', exportType='STL')
```

### 创建关节连杆
```python
# 球接头
joint = (
    cq.Workplane("XY")
    .sphere(5)                     # 球体
    .cut(cq.Workplane("XY").box(10, 10, 3, centered=(True, True, False)))  # 切平底部
)

# 插座
socket = (
    cq.Workplane("XY")
    .box(15, 15, 10)
    .faces(">Z").workplane()
    .hole(10.2)                    # 比球体大 0.2mm → 间隙配合
)

cq.exporters.export(joint, 'joint_ball.stl')
cq.exporters.export(socket, 'joint_socket.stl')
```

### 优缺点
| 优点 | 缺点 |
|------|------|
| 精确尺寸控制（0.01mm 级） | 不适合有机/自然形状 |
| 支持布尔运算、倒角、螺纹 | 学习曲线比 numpy-stl 陡 |
| 适合功能性零件 | 渲染预览不如 Blender 方便 |

## 3. fogleman/sdf — 数学公式建模

### 安装
```bash
pip install sdf
```

### 用法
```python
import sdf

# 使用 SDF 方程定义形状
f = sdf.sphere(1) & sdf.box(1.5)  # 球体切盒子

# 导出 STL
f.save('shape.stl', step=0.1)  # step 越小越精细
```

适合快速原型和算法生成的艺术造型。

## 4. meshio — 格式转换

### 安装
```bash
pip install meshio
```

### 用法
```python
import meshio

# 读取任何支持格式
mesh = meshio.read('model.stl')

# 导出为其他格式
meshio.write('model.obj', mesh)

# 支持的格式：STL, OBJ, PLY, OFF, STEP, VTK, XDMF 等数十种
```

## 工具链选择指南

**要做什么？** → **选什么工具？**

| 需求 | 工具 | 理由 |
|------|------|------|
| 打印前 STL 质检 | **trimesh** | 水密性、法线、尺寸一键检查 |
| 功能零件（支架、齿轮、连接件）| **CadQuery** | 精确参数化建模 |
| 数学/算法形状 | **sdf** | 最简洁的数学描述 |
| 有机形状 | **Blender bpy** | 细分曲面、曲线管线 |
| 格式转换 | **meshio** | 最全面的格式支持 |
| 布尔运算 | **trimesh** 或 **CadQuery** | 两者都支持，trimesh 更简单 |

## 推荐工作流

```
Blender (造型) → trimesh (布尔UNION合并/质检/修复) → 导出 STL → Bambu Studio/Orca Slicer
    或
Blender (布尔UNION一体式建模) → trimesh (质检) → 导出 STL → 切片
    或
Blender (造型) → Trimesh 质检 → CadQuery 补充精确卡扣 → trimesh 合并 → 切片
    或
CadQuery (参数化) → trimesh (质检) → 导出 STL → 切片
    或
sdf (算法生成) → trimesh (网格化+质检) → 切片
```

> **一体式打印工作流**：见 `3d-printing` 技能的`references/one-piece-boolean-union.md`——使用 Blender 布尔 UNION 将所有部件合并为一个水密 STL，加平板底座确保 Z=0 全平。Trimesh 可用于最终质检（水密性、体积、尺寸）。
```

### Blender → Trimesh 质检流水线

```bash
# 一次性安装全部
pip install trimesh cadquery sdf meshio vedo

# 验证
python3 -c "
import trimesh, cadquery, sdf, meshio
import numpy as np
print('✅ 所有 3D 工具链就绪')

# 快速测试 trimesh
m = trimesh.primitives.Sphere(radius=1)
print(f'测试球体: {len(m.faces)} 面, 水密: {m.is_watertight}')
"
```

## 关联技能

- **3d-printing** — 基础 STL 生成（numpy-stl 和 Blender 路径）
- **bambu-lab-tips** — 拓竹打印机设置和切片优化
