# One-Piece Boolean UNION Workflow (Blender)

## When to use this pattern

User needs a **single STL file** for an organic/character model where all body parts are physically connected (ears, limbs, tail fused to body) — **no assembly, no supports**. This replaces the multi-part articulated pattern.

## The session that produced this (TMNT Turtle, June 2026)

The user's cat model had 8 separate STL files + 201 separate connector files — assembly was tedious, parts didn't connect, and ears required supports. User demanded "一体打印" (one-piece print).

## Step-by-step recipe

### Phase 1: Build parts as separate objects

```python
import bpy
import math

def make_sphere_seg(name, radius, loc, segs=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=segs, ring_count=segs//2, location=loc)
    obj = bpy.context.object
    obj.name = name
    return obj

def make_ellipsoid(name, r, loc, segs=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=segs, ring_count=segs//2, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (r[0], r[1], r[2])
    bpy.ops.object.transform_apply(scale=True)
    return obj

# Build body parts — each MUST overlap the adjacent part
body  = make_ellipsoid("Body", (25, 30, 18), (0, 0, 0))
head  = make_sphere_seg("Head", 16, (0, 25, 12))         # overlaps body neck area
neck  = make_sphere_seg("Neck", 12, (0, 18, 20))          # bridge head↔body
leg_fl = make_ellipsoid("Leg_FL", (13, 18, 16), (-16, -10, -5))  # overlaps body
leg_fr = make_ellipsoid("Leg_FR", (13, 18, 16), (16, -10, -5))
leg_bl = make_ellipsoid("Leg_BL", (13, 18, 16), (-16, -25, -5))
leg_br = make_ellipsoid("Leg_BR", (13, 18, 16), (16, -25, -5))
tail  = make_ellipsoid("Tail", (8, 25, 8), (0, -36, -5))  # overlaps body
```

### Phase 2: Iterative boolean UNION

```python
def boolean_union(target_obj, tool_obj):
    """Merge tool_obj into target_obj via boolean UNION, then clean up"""
    mod = target_obj.modifiers.new(name=f"Bool_{tool_obj.name}", type='BOOLEAN')
    mod.operation = 'UNION'
    mod.solver = 'FLOAT'  # 'FAST' removed in Blender 5.x
    mod.object = tool_obj
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    
    # Clean up source object
    bpy.data.objects.remove(tool_obj, do_unlink=True)

# Merge all parts into body one by one
all_parts = [head, neck, leg_fl, leg_fr, leg_bl, leg_br, tail]  # body is the target
for part in all_parts:
    boolean_union(body, part)
```

### Phase 3: BMesh cleanup after UNION

```python
import bmesh

def cleanup_mesh(obj):
    """Remove doubles, recalc normals, fix non-manifold edges"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.holes_fill(bm, edges=bm.edges[:])
    
    bmesh.update_edit_mesh(me)
    bpy.ops.object.mode_set(mode='OBJECT')

cleanup_mesh(body)
```

### Phase 4: Flat base plate

```python
import numpy as np

# Find the Z range of the merged model
verts = np.array([v.co for v in body.data.vertices])
z_min = verts[:, 2].min()
z_max = verts[:, 2].max()

# XY bounds
x_min, x_max = verts[:, 0].min(), verts[:, 0].max()
y_min, y_max = verts[:, 1].min(), verts[:, 1].max()

# Add a rectangular base plate covering full XY footprint
plate_w = (x_max - x_min) * 1.1
plate_d = (y_max - y_min) * 1.1
plate_z_bot = z_min - 2.0
plate_z_top = z_min + 2.5  # ~4.5mm thick plate

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
plate = bpy.context.object
plate.name = "BasePlate"
plate.scale = (plate_w/2, plate_d/2, (plate_z_top - plate_z_bot)/2)
plate.location = (0, 0, (plate_z_bot + plate_z_top) / 2)
bpy.ops.object.transform_apply(scale=True, location=True)

# UNION plate into body
boolean_union(body, plate)
cleanup_mesh(body)
```

### Phase 5: Translate to Z=0

```python
# After plate is merged, translate so bottom is at Z=0
verts = np.array([v.co for v in body.data.vertices])
z_min = verts[:, 2].min()

bpy.ops.object.mode_set(mode='OBJECT')
for v in body.data.vertices:
    v.co.z -= z_min
```

### Phase 6: Export single STL

```python
# Apply subdivision for smoothness
mod = body.modifiers.new(name="SubSurf", type='SUBSURF')
mod.levels = 1
mod.render_levels = 1
bpy.ops.object.modifier_apply(modifier=mod.name)

# Smooth shading
for p in body.data.polygons:
    p.use_smooth = True

bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.wm.stl_export(
    filepath="output.stl",
    export_selected_objects=True,
    ascii_format=False,
    global_scale=10.0
)
```

## Verification commands

```bash
# 1. Check bounding box — all axes should be > 10mm
python3 -c "
import numpy as np
with open('output.stl', 'rb') as f:
    d = f.read()
nt = int.from_bytes(d[80:84], 'little')
verts = []
for i in range(nt):
    for j in range(3):
        v = np.frombuffer(d[84+i*50+12+j*12:84+i*50+24+j*12], dtype=np.float32)
        verts.append(v)
verts = np.array(verts)
print(f'{nt} tris')
print(f'X: {verts[:,0].min():.1f}~{verts[:,0].max():.1f}')
print(f'Y: {verts[:,1].min():.1f}~{verts[:,1].max():.1f}')
print(f'Z: {verts[:,2].min():.1f}~{verts[:,2].max():.1f}')
# Check Z=0 flatness
under_3mm = verts[verts[:,2] < 3.0]
print(f'Z<3mm: {len(under_3mm)} vertices' )
"

# 2. Verify bottom is flat (all bottom vertices should be at Z=0)
python3 -c "
import numpy as np
with open('output.stl', 'rb') as f:
    d = f.read()
nt = int.from_bytes(d[80:84], 'little')
z_vals = set()
for i in range(nt):
    for j in range(3):
        v = np.frombuffer(d[84+i*50+12+j*12:84+i*50+24+j*12], dtype=np.float32)
        if v[2] < 3:
            z_vals.add(round(v[2], 6))
print(f'Unique Z values under 3mm: {sorted(z_vals)}')
flat = len(z_vals) == 1 and 0.0 in z_vals
print(f'Bottom flat at Z=0: {flat}')
"

# 3. Check file size (should be > 10KB for meaningful model)
ls -la output.stl

# 4. Render preview (see 3d-printing skill's EEVEE渲染优化 section)
```

## Known pitfalls

| Problem | Solution |
|---------|----------|
| Boolean UNION fails on non-intersecting parts | Ensure every part's bounding box overlaps the target by 5mm+ |
| Boolean solver error: 'FAST' not found | Use `mod.solver = 'FLOAT'` (Blender 5.x removed 'FAST') |
| Vertices explode after UNION | Run `bmesh.ops.remove_doubles()` immediately after each UNION |
| STL has tiny fragments | Check for unmerged loose parts: `bpy.ops.mesh.separate_by_material()` and delete small pieces |
| Bottom not flat, Z varies < 3mm but not exactly 0 | Run the translate-to-Z=0 step after ALL booleans are done, including plate |
| Model is invisible in render | Check STL vertex bounds first (see debug-render-all-black.md), then check camera distance |

## Real-world example: TMNT Turtle (June 2026 session)

- 15 parts → 1 body via iterative UNION
- Base plate: 140×104×4.5mm (Z=-2~2.5mm)
- Final STL: 140×104×53mm, 6398 triangles, Z=0 flat throughout
- All vertices with Z<3mm: exactly at Z=0.0
- Verified with both numpy-stl header reader and trimesh
- Preview: EEVEE 1200×800, bright green material, light background
