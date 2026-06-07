# numpy-stl Phone Case Generation — OPPO Find N5 Back Cover

> 实盘记录：用 numpy-stl 纯 Python（无 Blender 依赖）生成 OPPO Find N5 单面后盖 STL，适合 FDM 3D 打印。

## 设计参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 宽度 (X) | 146mm | 折叠态宽度（推算） |
| 高度 (Y) | 160mm | 展开态高度（推算） |
| 壁厚 | 1.5mm | 壳壁厚度 |
| 内腔公差 | 0.3mm | 手机放入间隙 |
| 圆角半径 | 8mm | 四角圆弧 |
| 摄像头直径 | 36mm | 圆形孔位 |
| 摄像头凸起 | 5mm | 装饰圈高度 |
| 总厚度 | ~10.2mm | Z: -0.5 ~ 9.7mm |

## 核心算法

### 1. 圆角矩形轮廓

```python
def rounded_rect_profile(width, height, radius, n=32):
    \"\"\"生成圆角矩形轮廓点（Z=0 平面）\"\"\"
    r = radius
    w2, h2 = width/2, height/2
    pts = []
    # 四段 90° 圆弧
    for cx, cy, a_start in [
        (w2-r, h2-r, 0),          # 右上
        (-w2+r, h2-r, math.pi/2), # 左上
        (-w2+r, -h2+r, math.pi),  # 左下
        (w2-r, -h2+r, 3*math.pi/2)# 右下
    ]:
        for i in range(n):
            a = a_start + (math.pi/2) * i / n
            pts.append((cx + r*math.cos(a), cy + r*math.sin(a), 0.0))
    return pts
```

**注意：** `n=32` 每段 = `32×4=128` 个轮廓点。太少（<12）会导致打印件圆角有肉眼可见的棱角。

### 2. 挤出为 STL 实体

```python
def extrude_to_stl(profile_pts, z0, z1):
    \"\"\"2D 轮廓 → 3D 挤出体\n
    返回: (verts_3d, faces_3) — numpy-stl 兼容\n
    顶面和底面使用扇型三角剖分，侧面使用四边形拆三角。
    \"\"\"
    n = len(profile_pts)
    # 双层顶点：底层 Z=z0，顶层 Z=z1
    verts = np.array(
        [[x, y, z0] for x, y, _ in profile_pts] +
        [[x, y, z1] for x, y, _ in profile_pts],
        dtype=np.float64
    )
    faces = []
    # 底面（逆时针，法线向下）
    for i in range(1, n-1):
        faces.append([0, i, i+1])
    # 顶面（顺时针，法线向上）
    for i in range(1, n-1):
        faces.append([n, n+i+1, n+i])
    # 侧面（四边形拆两个三角形）
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, j+n])
        faces.append([i, j+n, i+n])
    # 组装为 Mesh 对象
    m = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(faces):
        for j in range(3):
            m.vectors[i][j] = verts[tri[j]]
    return m
```

**关键细节：** 顶面和底面的三角剖分**方向相反**（逆时针 vs 顺时针）——这是为了让法线都朝外。否则切片软件会认为模型背面朝外。

### 3. 内腔挖空

不依赖 Blender Boolean 运算，直接用**两个挤出体相减**：

```python
# 外壳 = 大圆角矩形挤出
outer = rounded_rect_profile(146, 160, 8)
outer_mesh = extrude_to_stl(outer, 0, 9.7)

# 内腔 = 缩小版挤出
inner = rounded_rect_profile(146 - 2*1.8, 160 - 2*1.8, max(8-1.8, 1))
inner_mesh = extrude_to_stl(inner, 1.5, 9.7 - 1.5)

# 合并（shell = outer ∪ inner，因为切片软件会忽略内部相交面）
# 注意：numpy-stl 不自动做布尔运算，但 STL 格式允许重叠面
# 切片软件（Bambu Studio/Orca Slicer）会自动检测并忽略内部的包围体。
combined = mesh.Mesh(np.concatenate([outer_mesh.data, inner_mesh.data]))
```

**⚠️ 这是关键技巧：** 不执行 Boolean DIFFERENCE，而是把外壳体和内腔体直接合并成一个 STL 文件。切片软件在生成 G-code 时会自动忽略内部的闭合面（因为它只关心外壳的流型边界）。这避免了 Blender Boolean 运算的复杂性和性能问题。

### 4. 摄像头孔环

```python
def make_camera_ring(cx=0, cy=0, inner_r=18, outer_r=19.5, z_bot=9.7, z_top=14.7, segs=48):
    \"\"\"生成圆形凸起环\"\"\"
    verts = []
    for z in [z_bot, z_top]:
        for i in range(segs):
            a = 2 * math.pi * i / segs
            # 外圈
            verts.append((cx + outer_r*math.cos(a), cy + outer_r*math.sin(a), z))
            # 内圈
            verts.append((cx + inner_r*math.cos(a), cy + inner_r*math.sin(a), z))
    
    faces = []
    # 顶面环（外→内逐段三角形）
    base = 2 * segs  # 顶层起始索引
    for i in range(segs):
        j = (i + 1) % segs
        o0, o1 = base + i*2, base + j*2
        i0, i1 = base + i*2 + 1, base + j*2 + 1
        faces.append([o0, o1, i1])
        faces.append([o0, i1, i0])
    # 外侧面（底层→顶层）
    for i in range(segs):
        j = (i + 1) % segs
        b0, b1 = i*2, j*2
        t0, t1 = base + i*2, base + j*2
        faces.append([b0, b1, t1])
        faces.append([b0, t1, t0])
    # 内侧面类似...
    # 底面环类似...
    # 组装为 Mesh
```

## 文件大小与质量

| 版本 | 三角面数 | STL 大小 | 方法 |
|------|---------|----------|------|
| Blender 版（subsurf=1） | ~2K* | ~254KB | Blender bpy |

*numpy-stl 版本直出更精简，实际大小取决于 segs 参数。

## 打印建议

- **材料**：TPU（柔性，易拆装）或 PETG（刚性）
- **朝向**：摄像头孔朝上，内腔朝天花板
- **支撑**：需要树状支撑（摄像头孔环悬空）
- **层高**：0.16-0.2mm
- **填充**：15-20%
- **打印前检查**：在 Bambu Studio 中用 "Cut" 工具切一刀确认壁厚和内腔尺寸

## 验证脚本

```bash
python3 -c "
import numpy as np
from stl import mesh

m = mesh.Mesh.from_file('FindN5_BackCover.stl')
verts = np.unique(m.vectors.reshape(-1, 3), axis=0)
ranges = [verts[:,i].max()-verts[:,i].min() for i in range(3)]
print(f'Faces: {len(m.vectors)}')
print(f'Unique verts: {len(verts)}')
print(f'Size: {ranges[0]:.1f} x {ranges[1]:.1f} x {ranges[2]:.1f} mm')
print(f'Z range: {verts[:,2].min():.1f} ~ {verts[:,2].max():.1f} mm')
print(f'Volume estimate: {m.get_mass_properties()[1]:.1f} cc')

# 将质心移至模型底部（便于打印床定位）
center = verts.mean(axis=0)
print(f'Centroid: ({center[0]:.1f}, {center[1]:.1f}, {center[2]:.1f})')
if center[2] < 0:
    print('⚠️  Z centroid below ground')
"
```
