---
name: 3d-printing
description: "Generate FDM-ready 3D printable STL models — one-piece boolean-UNION character models (Blender), multi-part articulated designs (numpy-stl), phone cases, and custom parts. Covers the full pipeline: modeling → boolean merge → flat base plate → STL export → render preview → bed adhesion verification."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [3d-printing, stl, fdm, cad, generative-design, articulated, multi-part, numpy-stl, blender, boolean-union, one-piece, character-modeling, phone-case]
    related_skills: [sketch, spike, python-3d-tools, bambu-lab-tips]
---

# 3D Printing — Generative STL Models from Python

Use this skill when the user wants to **3D print a custom object** — an articulated toy, a functional part, a decorative model — and asks you to create the STL file(s). The approach uses `numpy-stl` to build geometry from basic primitives (sphere, cylinder, cone, extrusion) and export as `.stl` files ready for Bambu Studio / Orca Slicer / Cura.

## When to use this

- User says "design a 3D model of X" or "make something I can print"  
- User has a Bambu Lab / Creality / Prusa / Anycubic FDM printer  
- The model can be **one-piece** (single STL, boolean-UNION merged — preferred for maximum simplicity)  
- Multi-part articulated designs (joints, hinges, snap-fits) — export as separate STL files only if user explicitly asks for movable parts  
- Phone cases (foldable or single-back) using the numpy-stl extrusion pattern  
- The model can be approximated as **combinations of basic geometric shapes** (spheres, cylinders, cones, extrusions) when using numpy-stl  

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

### 3. Multi-part articulated design pattern

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

### ⚠️ 渲染可见性 — 避免"全黑图"的首要原则

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

## Verification

After generating STLs (do this BEFORE rendering or sending to user):

> For one-piece boolean UNION models, see `references/one-piece-boolean-union.md` for the dedicated verification procedure including bottom-flatness check and vertex-range analysis.
> For cartoon character models (animals, mascots, action figures), see `references/cartoon-character-modeling.md` for the complete part-inventory checklist and feature-building guide — run the verification script there before sending to the user.

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

- **numpy-stl's Mode**: Must import `from stl import Mode` explicitly, then use `Mode.BINARY` / `Mode.ASCII`. ASCII mode is readable but ~5x larger — only use for debugging.
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
- **Vision unavailable protocol**: When `vision_analyze` fails (401/400) or AI vision can't identify a render: (1) check STL vertex bounds first, (2) generate 2D line-art preview with Pillow (no Blender), (3) send raw files to user via MEDIA: for them to see directly.
