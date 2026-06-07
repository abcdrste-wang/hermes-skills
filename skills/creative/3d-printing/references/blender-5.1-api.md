# Blender 5.1 Python API — 3D Printing Patterns

Captured from real headless Blender usage on macOS (Apple Silicon M4, brew-installed Blender 5.1.2). API quirks and patterns discovered during a multi-part articulated cat model project.

## Installation

```bash
brew install --cask blender
# → /Applications/Blender.app
# → /opt/homebrew/bin/blender
```

## Headless running

```bash
# Run a script
blender --background --python script.py

# Run a one-liner
blender --background --python-expr "import bpy; print(bpy.app.version_string)"

# Pipe output: use 2>&1 to capture blender's stdout (info messages go to stdout)
blender --background --python script.py 2>&1 | tail -10
```

## API quirks (Blender 5.0 → 5.1 migration)

### STL export (broken in 5.1)

**WRONG (pre-5.0 API):**
```python
bpy.ops.wm.stl_export(
    filepath=path,
    export_selected_objects=True,
    ascii_format=False,
    scale_unit='MILLIMETERS',   # REMOVED in 5.x → TypeError
    global_scale=10.0
)
```

**RIGHT (5.0+ API):**
```python
bpy.ops.wm.stl_export(
    filepath=path,
    export_selected_objects=True,
    ascii_format=False,
    global_scale=10.0           # scale_unit gone; 10.0 = mm
)
```

### Render engine enum (renamed in 5.x)

**WRONG:**
```python
bpy.context.scene.render.engine = 'EEVEE'  # → TypeError: enum not found
```

**RIGHT:**
```python
bpy.context.scene.render.engine = 'BLENDER_EEVEE'  # or 'CYCLES', 'BLENDER_WORKBENCH'
```

### Material nodes (deprecated in 6.0)

```python
# Works in 5.1 but triggers DeprecationWarning
mat.use_nodes = True          # Will be removed in Blender 6.0
```

Workaround: set materials using the now-preferred API (in Blender 5.x this still requires legacy `use_nodes`).

## Multi-part model building patterns

### Subdivision Surface (Subsurf)

```python
mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
mod.levels = 1          # level 1 for 3D printing (level 2 = 4x triangles)
mod.render_levels = 1
```

**Apply before STL export:**
```python
for mod in obj.modifiers:
    if mod.type == 'SUBSURF':
        bpy.ops.object.modifier_apply(modifier=mod.name)
```

### Curve → Mesh workflow (for tails, whiskers, curved parts)

```python
import mathutils

# 1. Create curve data
curve_data = bpy.data.curves.new('tail_curve', type='CURVE')
curve_data.dimensions = '3D'
curve_data.resolution_u = 8

# 2. Add bezier points
spline = curve_data.splines.new('BEZIER')
spline.bezier_points.add(4)
for i, pos in enumerate([(0,0,0), (-0.5,0.3,0), (-1.0,0.8,0)]):
    p = spline.bezier_points[i]
    p.co = mathutils.Vector(pos)
    p.handle_left_type = 'AUTO'
    p.handle_right_type = 'AUTO'
    p.radius = 0.25 * (1 - i * 0.15)

# 3. Set tube geometry via bevel
curve_data.bevel_depth = 0.15
curve_data.bevel_resolution = 3
curve_data.use_fill_caps = True

# 4. Create object and link to collection
curve_obj = bpy.data.objects.new('tail', curve_data)
bpy.context.collection.objects.link(curve_obj)

# 5. Convert to mesh (mandatory before Subsurf/STL export)
bpy.ops.object.select_all(action='DESELECT')
curve_obj.select_set(True)
bpy.context.view_layer.objects.active = curve_obj
bpy.ops.object.convert(target='MESH')         # ← Crucial! Curves have no polygons
```

**CRITICAL: Curves do NOT have `.data.polygons`.** Calling `create_part()` (which iterates polygons) on a curve object will raise `AttributeError: 'Curve' object has no attribute 'polygons'`. Always convert to mesh first.

### Smooth shading

```python
for poly in obj.data.polygons:
    poly.use_smooth = True
```

### Camera + render for preview images

```python
import math

# Add camera
bpy.ops.object.camera_add(location=(6, -4, 4))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(60), 0, math.radians(30))
bpy.context.scene.camera = cam

# Add lights
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
bpy.context.object.data.energy = 3

# Render
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.filepath = "/tmp/preview.png"
bpy.ops.render.render(write_still=True)
```

## Performance notes (Mac Mini M4, 16GB)

| Operation | Time |
|-----------|------|
| Blender startup (headless) | 3-4s |
| Import assembled STL (14MB, ~150K faces) | 264ms |
| EEVEE render (1920×1080, one Sun light) | 1.8-6s |
| STL export per part (small <2K faces) | ~3.9ms |
| STL export per part (large ~50K faces) | ~16ms |
| bpy.ops.convert (curve→mesh) | ~2ms |
| Script total (build 10 parts + export) | 5-8s |

## File size reference (level 1 subdivision)

| Part | Base mesh complexity | STL size |
|------|---------------------|----------|
| Body (sphere, 32×24 → subdiv 1) | ~1K faces | 3.0 MB |
| Head (sphere, 32×24 → subdiv 1) | ~1K faces | 3.0 MB |
| Leg (cylinder, 12 seg → subdiv 1) | ~600 faces | 1.8 MB |
| Ear (cone, 8 seg → subdiv 1) | ~300 faces | 19 KB |
| Tail (curve bezier, 5pt → subdiv 1) | ~500 faces | 519 KB |

Level 2 subdivision produces ~4× the triangles and STL size.

## Error catalog

| Error | Cause | Fix |
|-------|-------|-----|
| `TypeError: keyword "scale_unit" unrecognized` | Using pre-5.0 STL export | Remove `scale_unit` param |
| `TypeError: enum "EEVEE" not found` | 5.x renamed engines | Use `'BLENDER_EEVEE'` |
| `AttributeError: 'Curve' object has no attribute 'polygons'` | Applying mesh ops to curve | `.convert(target='MESH')` first |
| `TypeError: enum "GEOMETRY_NODES" not found` | Wrong enum value for node tree | Use `'GeometryNodeTree'` not `'GEOMETRY_NODES'` |

## Background-mode camera positioning & pitfalls

### `scene.camera is None` bug

**Problem:** After clearing the scene (`bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)`), `scene.camera` becomes `None`. Calling `bpy.ops.object.camera_add()` creates a new camera object but **does NOT automatically set `scene.camera`** — it sets `bpy.context.view_layer.objects.active = camera_obj` but leaves `scene.camera = None`.

```python
# WRONG: camera_add does NOT set scene.camera
bpy.ops.object.camera_add(location=(5, -5, 5))
cam = bpy.context.active_object  # Fine
# scene.camera is still None!

# RIGHT: always set explicitly after creating camera
bpy.ops.object.camera_add(location=(5, -5, 5))
cam = bpy.context.active_object
bpy.context.scene.camera = cam   # ← MUST do this
```

**Detection:** A render with `scene.camera = None` creates a default isometric view from (0, -5, 5) looking at origin — but the resolution may be wrong and `bpy.ops.render.render()` may silently use a fallback view. Always verify `bpy.context.scene.camera is not None` before rendering.

### Camera distance for proper framing

When manually positioning the camera in background mode (no `view3d` viewport to preview), use this formula:

```python
import math

def frame_camera(obj, camera, fill_ratio=0.6):
    \"\"\"Position camera so obj fills ~60% of frame\"\"\"\
    bounds = obj.dimensions
    max_dim = max(bounds.x, bounds.y, bounds.z)
    # Camera at 45-degree isometric angle
    dist = max_dim / (2 * math.tan(math.radians(camera.data.angle / 2))) / fill_ratio
    camera.location = (dist * 0.7, -dist * 0.7, dist * 0.5)
    # Point at world origin (assumes model centered at 0,0,0)
    direction = mathutils.Vector((-camera.location.x, -camera.location.y, -camera.location.z)).normalized()
    up = mathutils.Vector((0, 0, 1))
    quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = quat.to_euler()
    return camera
```

### Z-axis position: model must be above ground

**Critical:** If the STL model has Z vertices below 0, a camera positioned at Z>0 looking at (0,0,0) will be looking ABOVE the model. Always verify STL Z range before rendering:

```bash
# Quick check: STL Z centroid should be > 0
python3 -c "
import numpy as np
with open('model.stl', 'rb') as f:
    data = f.read()
num_tris = int.from_bytes(data[80:84], 'little')
verts = []
for i in range(num_tris):
    offset = 84 + i * 50
    for j in range(3):
        v = np.frombuffer(data[offset+12+j*12:offset+24+j*12], dtype=np.float32)
        verts.append(v)
verts = np.array(verts)
print(f'Z range: {verts[:,2].min():.1f} ~ {verts[:,2].max():.1f}')
if verts[:,2].mean() < 0:
    print('⚠️  Model Z centroid is below ground — camera looking at (0,0,0) will miss it!')
"
```

### Translating STL after import (Z fix)

If the STL was generated with Z range below 0 (e.g., Z: -0.5 ~ 9.7), translate it up:

```python
# After importing STL
obj = bpy.context.active_object
# Check if below ground
if obj.location.z + obj.dimensions.z / 2 < 0:
    # Translate so bottom sits at z=0
    min_z = min(v.co.z for v in obj.data.vertices)
    obj.location.z = -min_z  # Now bottom = 0
```

## Multi-angle render preview pattern

When the user asks to see the model, generate 4 separate JPEG images (800x600, quality=85) from different angles rather than one large composite. This avoids Feishu/Telegram thumbnail cropping issues.

```python
angles = [
    ("front",   0, -3, 2),    # (label, cam_x, cam_y, cam_z)
    ("45deg",  3.5, -2.5, 2),
    ("side",    5,   0,   2),
    ("top",     0,   0,   5),
]

for label, cx, cy, cz in angles:
    bpy.ops.object.camera_add(location=(cx, cy, cz))
    cam = bpy.context.active_object
    # Point camera at origin (0,0,0)
    direction = (-cx, -cy, -cz)
    import mathutils
    quat = mathutils.Vector((0, 0, -1)).rotation_difference(mathutils.Vector(direction))
    cam.rotation_euler = quat.to_euler()

    # IMPORTANT: multiply camera distance by 2x to ensure full model fits in frame
    cam.location *= 2.0

    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = f"/tmp/view_{label}.jpg"
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
```

**Key insight**: Models with subdivision surfacing appear physically larger in the viewport than their base mesh coordinates suggest. Always multiply the intuitive camera distance by 2x for a safe framing. Send each angle as a separate message (Feishu renders MEDIA: inline but may crop large images).

### Feishu-specific delivery pattern

When sending rendered previews to Feishu:
1. Use JPEG (smaller than PNG, renders inline reliably)
2. Keep resolution moderate (800x600)
3. Send each angle as a separate message with a descriptive label
4. Refer to the corresponding STL files already sent so the user can correlate
