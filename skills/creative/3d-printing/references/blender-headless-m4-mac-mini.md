# Blender 5.1.2 Headless on M4 Mac Mini — 已知问题与避坑指南

## 环境
- Mac: Mac Mini M4 (16GB), macOS 26.5.1
- Blender: 5.1.2 (从 blender.org 下载官方 arm64 版，非 brew)
- 运行模式: `blender --background` (headless)
- 显卡: Apple M4 (无独立 GPU)，Metal API
- Shell: bash (+zsh)

## 已知硬坑（已验证）

### 1. EEVEE 渲染输出纯黑帧
- **症状**: `bpy.ops.render.render(write_still=True)` 输出全黑 PNG（所有像素 RGB(0,0,0)）
- **根因**: M4 无独立 GPU，EEVEE 在 headless Metal 下无法获取帧缓冲
- **检测方法**: 渲染后用 PIL 统计非黑像素占比，全黑则自动降级
- **解决方案**:
  - 默认使用 `stl_2d_preview.py`（PIL + numpy-stl，线框投影）作为首选渲染方式
  - 仅当用户明确要求彩色渲染时才尝试 EEVEE，且渲染后必须自动检测
  - 备选：Cura 切片预览（见 `cura-as-render-alternative.md`）

### 2. modifier_apply 静默失败
- **症状**: `obj.modifiers.new(name, type).apply()` 返回成功但几何体**无任何变化**
- **影响的 modifier 类型**: SUBSURF, MIRROR, BOOLEAN, ARRAY, BEVEL （全部不可用）
- **根因**: headless 模式下某些 modifier 依赖于 GPU/视口上下文
- **解决方案**:

#### SUBSURF → bmesh.subdivide_edges
```python
import bmesh
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.edges.ensure_lookup_table()
# subdivide_edges(edges, cuts, use_grid_fill)
# cuts=2 相当于 Subdivision Surface level 2
bm_sub = bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=2, use_grid_fill=True)
bm.to_mesh(obj.data)
bm.free()
```

#### MIRROR → bmesh_symmetrize_mirror
```python
bm = bmesh.new()
bm.from_mesh(obj.data)
# 沿 X 轴对称
bmesh.ops.symmetrize(bm, input=bm.verts[:], direction='POSITIVE_X')
bm.to_mesh(obj.data)
bm.free()
```

#### BOOLEAN 替代
- 使用 Trimesh 或 numpy-stl 在 Python 中做布尔运算
- 或将两个 STL 在外部拼接后重新导入

#### ARRAY → 手动循环复制
```python
import bpy, mathutils
for i in range(count):
    copy = obj.copy()
    copy.data = obj.data.copy()
    copy.location.x += i * spacing
    col.objects.link(copy)
```

### 3. 渲染全黑排错步骤
见 `debug-render-all-black.md`

### 4. Blender 5.x API 差异
- modifier names 从 "Subsurf" 改为 "Subdivision Surface"
- `bpy.ops.object.shade_smooth()` 可正常使用
- 见 `blender-5.1-api.md` 和 `blender-5x-modifier-names.md`

## 推荐的 M4 3D 建模范式
| 任务类型 | 推荐工具 | 原因 |
|---------|---------|------|
| 管状/有机体 (能量剑、触手) | CadQuery + numpy-stl | 椭圆截面堆叠，绕开所有 Blender |
| 轮廓型 (枪械侧面) | Blender 轮廓挤出 | 只需基础几何，绕开 modifier |
| 渲染预览 | stl_2d_preview.py (PIL) | 可靠，不依赖 GPU |
| 角色卡通 | Blender + Trimesh | 面数要求在 3000-5000+，使用 bmesh 替代 modifier |
