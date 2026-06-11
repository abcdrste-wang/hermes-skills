# Approved-Model Contour Rebuild Pattern

> **Case: FFAR1 无境空刃 detail_v1, June 2026**
> 
> User had seen and approved an "energy blade" silhouette shape (from an earlier rebuild v4/v5), but said the model was still rough. Instead of iterating on the box-composition approach, we:
> 1. Rendered the approved model from side view
> 2. Extracted its silhouette contour from the render PNG
> 3. Used that contour as the side-profile for a fresh side-extrusion rebuild
> 4. Added cylinder/disc/muzzle details on top of the clean silhouette
> 5. Result: detail_v1 (362 vertices, 720 faces) — cleaner geometry and correct silhouette

## When to Use This Pattern

Use this when:
- User has seen a model and says "it's getting there but still rough"
- The current model has the right silhouette but wrong construction (e.g., box composition or otherwise bad topology)
- You need to rebuild the model from scratch but preserve the approved overall shape
- The original reference image is ambiguous or unusable for direct contour extraction

## Pattern Diagram

```
Current model (rough, approved silhouette)
  → render side-view PNG
  → extract contour from PNG (dark pixels on light/transparent bg)
  → Gaussion smooth contour
  → downsample to 120-200 points
  → bmesh side-extrude to create clean geometry
  → add details (cylinder/cone/disc primitives) via bmesh or trimesh union
  → verify against user's original reference and approved silhouette
  → send to user
```

## Prerequisites

| Tool | Purpose |
|------|---------|
| PIL/Pillow | Read render PNG, extract pixel coordinates |
| numpy | Gaussian smoothing (no scipy needed) |
| Blender | bmesh side-extrude the contour |
| stl_2d_preview.py | Render side view of current model |

## Step-by-Step

### 1. Render Current Model Side-View

```bash
python3 stl_2d_preview.py current_model.stl -o current -v side
```

Output: `current_side.png` — light background, dark outline of the model.

### 2. Extract Contour from Render PNG

```python
import numpy as np
from PIL import Image

def extract_contour_from_render(png_path, num_samples=160):
    """
    Extract object contour from a render PNG.
    Works with stl_2d_preview output (dark outline on white bg).
    Returns: (left_contour, right_contour) as array of (x, y) or None
    """
    img = Image.open(png_path).convert('RGBA')
    arr = np.array(img)
    h, w = arr.shape[:2]
    
    # Create binary mask: object pixels (not-white, not-transparent)
    alpha = arr[:, :, 3] > 128
    rgb = arr[:, :, :3]
    is_non_bg = (rgb.max(axis=2) < 240) & alpha
    
    # Find leftmost and rightmost object pixel at each row
    left = []
    right = []
    
    for y in range(h):
        row = is_non_bg[y, :]
        obj_pixels = np.where(row)[0]
        if len(obj_pixels) > 0:
            left.append((int(obj_pixels[0]), y))
            right.append((int(obj_pixels[-1]), y))
    
    if not left:
        print("⚠️ No object pixels found in render! Check background threshold.")
        return None, None
    
    # Sample to desired number
    def sample(pts, n):
        pts = np.array(pts, dtype=float)
        if len(pts) < n:
            return pts
        indices = np.linspace(0, len(pts)-1, n, dtype=int)
        return pts[indices]
    
    return sample(left, num_samples), sample(right, num_samples)
```

### 3. Smooth and Prepare Contour

```python
def gaussian_kernel_1d(sigma=3.0):
    """1D Gaussian kernel (no scipy needed)"""
    size = int(6 * sigma) | 1
    x = np.arange(-(size//2), size//2 + 1)
    kernel = np.exp(-x**2 / (2 * sigma**2))
    return kernel / kernel.sum()

def smooth_contour(points, sigma=3.0):
    """Gaussian smooth a contour"""
    pts = np.array(points)
    kernel = gaussian_kernel_1d(sigma)
    pad = len(kernel) // 2
    px = np.pad(pts[:, 0], pad, mode='edge')
    py = np.pad(pts[:, 1], pad, mode='edge')
    sx = np.convolve(px, kernel, mode='valid')
    sy = np.convolve(py, kernel, mode='valid')
    return np.column_stack([sx, sy])
```

### 4. Verify Smoothed Contour Overlay

Before feeding to Blender, always check:

```python
# Overlay smoothed contour on the original render
from PIL import ImageDraw
img = Image.open('current_side.png').convert('RGBA')
draw = ImageDraw.Draw(img)
for x, y in smoothed_left:
    draw.ellipse([x-2, y-2, x+2, y+2], fill='red')
img.save('contour_check.png')
```

**Check:** Does the smoothed contour follow the original object outline? Red dots should closely trace the object edges with < 5px deviation. If they drift off (e.g., through transparent areas), adjust the threshold in step 2 or use manual masking.

### 5. Build Blender Side-Extrusion from Contour

```python
import bpy
import bmesh
import numpy as np

def build_from_contour(left_pts, right_pts, thickness=10.0,
                       center_x=0, center_y=0, center_z=0):
    """
    Build a 3D mesh using BOTH left and right contours.
    Convention: image X → 3D X, image Y → 3D Z
    thickness → 3D Y (extrusion depth)
    """
    mesh = bpy.data.meshes.new("FromApprovedContour")
    bm = bmesh.new()
    
    # Left contour becomes the "front" face (Y = -thickness/2)
    # Right contour becomes the "back" face (Y = +thickness/2)
    N = len(left_pts)
    front_verts = []
    back_verts = []
    
    # Center: subtract midpoint so model centers at origin
    all_xy = np.vstack([left_pts, right_pts])
    x_mean, y_mean = all_xy.mean(axis=0)
    
    for x, y in left_pts:
        front_verts.append(bm.verts.new((
            x - x_mean + center_x,
            -thickness / 2 + center_y,
            y - y_mean + center_z
        )))
    
    for x, y in right_pts:
        back_verts.append(bm.verts.new((
            x - x_mean + center_x,
            thickness / 2 + center_y,
            y - y_mean + center_z
        )))
    
    # Connect front → back
    for i in range(N - 1):
        bm.faces.new([
            front_verts[i], front_verts[i+1],
            back_verts[i+1], back_verts[i]
        ])
    
    # Close the ends (top/bottom of the 3D shape)
    # Top: last verts of front and back
    bm.faces.new([front_verts[-1], back_verts[-1], back_verts[0], front_verts[0]])
    # Bottom: first verts of front and back
    bm.faces.new([front_verts[0], back_verts[0], back_verts[-1], front_verts[-1]])
    
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new("BaseProfile", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

# Usage
left, right = extract_contour_from_render('current_side.png', num_samples=200)
if left is not None:
    left_smooth = smooth_contour(left, sigma=3.0)
    right_smooth = smooth_contour(right, sigma=3.0)
    obj = build_from_contour(left_smooth, right_smooth, thickness=8.0)
```

### 6. Add Details on Top of the Clean Base

After the base silhouette is built, add cylinder/disc/cone primitives as separate objects, then join (not boolean UNION — join is sufficient for 3D printing):

```python
# Add cylinders for muzzle, grips, etc.
bpy.ops.mesh.primitive_cylinder_add(
    radius=3.0, depth=4.0,
    location=(0, 0, muzzle_z),
    rotation=(1.5708, 0, 0)  # rotate to align with extrusion
)
cylinder = bpy.context.object

# Combine: select all objects, join
bpy.ops.object.select_all(action='DESELECT')
base_obj.select_set(True)
cylinder.select_set(True)
bpy.context.view_layer.objects.active = base_obj
bpy.ops.object.join()

# Export
bpy.ops.wm.stl_export(
    filepath='detail_v1.stl',
    export_selected_objects=True
)
```

## Face Count Budget

| Stage | Target Faces | Purpose |
|-------|-------------|---------|
| Base contour (160 pts, 2-sided) | ~640 | Clean silhouette, no visible faceting |
| With subsurf (bmesh, 1x) | ~2,560 | Smooth curves, detail-ready |
| With 2-3 primitive additions | ~3,000-5,000 | Game-weapon-quality detail level |
| **Detail_v1 target** | **~1,000-2,000** | First detail pass: silhouette + key features |

**Key lesson from FFAR1 detail_v1:** 362 vertices / 720 faces was enough to show the correct silhouette to the user, but lower than ideal for fine detail. Target 1000-2000 faces for first detail pass.

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **Contour from single-side render misses 3D depth** | Model looks "flat" (same thickness all along) | Use multiple reference views; adjust thickness per region |
| **Render contour includes background noise** | Jagged edges on smooth parts | Check threshold in step 2; increase sigma in step 3 |
| **Contour from low-res render** (< 300px) | Blocky, aliased contour | Render at higher resolution; use smoothing but accept minor aliasing |
| **Left and right contours swap** | Model faces wrong direction | Verify: in side view, left contour = object's front (closer to camera), right = back |
| **Model top includes empty space** | Extra flat faces at tip | Trim the top/bottom of the contour: remove the first/last 5% of points where the left and right contours converge |
