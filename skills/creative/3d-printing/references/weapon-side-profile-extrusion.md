# Weapon Model: Side-Profile Extrusion Method (Blender bmesh)

## When to use this

**Any weapon/mecha/vehicle model where the side silhouette defines identity.**

This is the CORRECT starting method for:
- Guns (rifles, pistols, SMGs, shotguns)
- Mecha limbs
- Vehicle profiles (tanks, ships seen from side)
- Any object where profile recognizability > surface detail

**Do NOT use box composition (numpy-stl) for these objects.** Box composition produces unrecognizable shapes regardless of face count (proven across v1=780, v2=276, v3=5712 faces — all failed for FFAR1).

## Core concept

1. Define the **2D side-profile contour** using pixel-coordinate points from a reference image
2. Build a **bmesh polygon** from those points (no triangles, just one flat polygon)
3. **Extrude** the polygon to give it thickness
4. Add **detail blocks** (sights, magazine, trigger guard, muzzle) as separate bmesh objects
5. **Join** all objects into one mesh

## Step-by-step process

### 1. Contour point extraction

From a reference image (e.g., side-view photo of the weapon):

```python
# Define contour points as (x, y) pixel coordinates from reference image
# Convention: Y-axis = long axis of weapon (barrel direction)
# X-axis = vertical axis (height of weapon)
# Origin (0,0) at top-left or compatible with image coordinates

# == Contour point groups ==
BARREL_CONTOUR = [
    (0.18, 4.32), (0.18, 5.12), (0.28, 5.12),  # muzzle
    (0.28, 1.92),  # barrel top
    (0.24, 1.72),  # gas block transition
    (0.30, 1.40),  # handguard top
]
RECEIVER_CONTOUR = [
    (0.30, 1.40), (0.54, 1.20),  # receiver top
    (0.54, 0.00),  # rear
    (0.30, 0.40), (0.30, 0.90),  # grip junction
]
GRIP_CONTOUR = [
    # angled grip
    (0.30, 0.90), (0.33, 0.50), (0.40, 0.16),
    (0.42, 0.08), (0.40, 0.00), (0.36, -0.04),  # grip bottom
    (0.26, -0.02), (0.24, 0.20), (0.22, 0.70),  # grip rear
]
# ... etc for stock, magazine, trigger guard
```

**Key rules for contour points:**
- Points must trace the **exterior boundary** of the weapon — top profile → muzzle → bottom profile → rear
- **Minimum 30-50 points** for a recognizable weapon (FFAR1 v4 had 47, v5 had 124)
- Include all major bumps and features: sights, magazine well, trigger guard arc, stock comb
- Points are **ordered** — they will become a single polygon

### 2. Normalize and scale

```python
import numpy as np
import bpy, bmesh, math

# Convert pixel coords to mesh coords
# Z-axis = height (was X in pixel coords)
# Y-axis = length (was Y in pixel coords)
# X-axis = thickness

# Step 1: normalize to 0-1 range
norm_pts = []
xs = [p[0] for p in contour_pts]
ys = [p[1] for p in contour_pts]
min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)
for px, py in contour_pts:
    nx = (px - min_x) / (max_x - min_x)  # height (Z in 3D)
    ny = (py - min_y) / (max_y - min_y)  # length (Y in 3D)
    norm_pts.append((nx, ny))

# Step 2: scale to desired size (e.g., target_length = 140mm)
target_length = 140.0  # mm
target_height = target_length * (max_x - min_x) / (max_y - min_y)
for i, (nx, ny) in enumerate(norm_pts):
    z = nx * target_height  # height
    y = ny * target_length  # length
    norm_pts[i] = (z, y)  # now (Z, Y) in 3D space
```

### 3. Build polygon and extrude

```python
def build_weapon_profile(contour_pts_3d, thickness=14.0, name="Weapon"):
    """
    Build a weapon from side-profile contour.
    contour_pts_3d: list of (z, y) tuples defining the profile boundary
    thickness: how thick the weapon is (X axis in mm)
    """
    bm = bmesh.new()
    
    # Create vertices at z=0 plane
    top_verts = []
    for z, y in contour_pts_3d:
        top_verts.append(bm.verts.new((0, y, z)))
    
    # Create face from top profile
    # blensor_faces expects clockwise winding for visible side
    # For weapon profile traced clockwise: top→muzzle→bottom→rear
    # This naturally gives correct winding for the +X facing side
    top_face = bm.faces.new(top_verts)
    
    # Flip normal if needed
    # top_face.normal_flip()
    
    # Extrude by thickness to create 3D solid
    extruded = bmesh.ops.extrude_face_region(bm, geom=[top_face])
    
    # Translate extruded vertices in X direction
    extruded_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]
    translate_vec = (thickness, 0, 0)
    bmesh.ops.translate(bm, vec=translate_vec, verts=extruded_verts)
    
    # Close the mesh by creating side faces and end caps
    # The extrude_face_region already creates side walls and caps
    # Just need to ensure manifold
    
    return bm

# Usage:
# bm = build_weapon_profile(contour_pts_3d, thickness=14.0)
# mesh = bpy.data.meshes.new("WeaponProfile")
# bm.to_mesh(mesh)
# bm.free()
# obj = bpy.data.objects.new("WeaponProfile", mesh)
# bpy.context.collection.objects.link(obj)
```

### 4. Add detail parts

Weapons have distinct detail parts that don't come from the profile. Add these as **separate bmesh objects**, then join all:

```python
def add_detail_part(parts_list, bm_func, **kwargs):
    """Build a detail part and add to parts list for later joining"""
    bm = bm_func(**kwargs)
    me = bpy.data.meshes.new(kwargs.get('name', 'part'))
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(kwargs.get('name', 'part'), me)
    bpy.context.collection.objects.link(obj)
    parts_list.append(obj)
    return obj

# Common detail parts:
# - Magazine: small extruded rectangle, placed at mag well location
# - Trigger guard: tiny loop profile, extruded thin
# - Front sight: small post with protective ears
# - Rear sight: small flat block with notch
# - Muzzle brake: slightly wider cylinder at muzzle tip
# - Foregrip: small angled block under handguard
```

### 5. Join all parts

```python
def join_all(parts_list, name="WeaponMerged"):
    """Select all parts and join into one mesh"""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts_list:
        obj.select_set(True)
    
    # First object becomes the active (master) object
    master = parts_list[0]
    bpy.context.view_layer.objects.active = master
    bpy.ops.object.join()
    
    master.name = name
    master.data.name = name
    return master
```

### 6. Export STL

```python
def export_stl(obj, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(
        filepath=filepath,
        export_selected_objects=True,
        ascii_format=False,
        global_scale=10.0  # Blender 5.x: no scale_unit param
    )
```

## Complete working example (FFAR1 v4 — 47 points, 49 faces)

See the session transcripts for the full v4 script at `~/.hermes/scripts/blender_ffar1_v4.py` (compact version) and `ffarl_v5.py` (124-point detailed version).

The v4 script demonstrates:
- 47 contour points extracted from reference image
- Single bmesh polygon → face → extrude → thickness
- ~10 detail blocks (magazine, trigger guard, grip, stock, sights)
- Total: 49 faces, ~22KB STL
- Silhouette immediately recognizable as a rifle

## Critical Pitfalls

1. **Points must form a non-self-intersecting polygon.** If the contour crosses itself, `bm.faces.new()` raises `ValueError: duplicate verts` and the polygon is rejected. Check your contour ordering carefully — clockwise around the entire weapon boundary.

2. **Too few contour points = faceted silhouette.** 47 points (v4) was enough to be recognizable but looked crude. 124 points (v5) is the recommended minimum for a weapon with curved details (stock comb, grip contour, handguard shape).

3. **Extrusion thickness varies by part.** A rifle typically has barrel thickness = 8-10mm, receiver/stock thickness = 14-18mm, grip thickness = 12-14mm. For single extrusion you pick a compromise; for multi-thickness models, build the barrel and receiver as separate extrusions and merge them.

4. **On-axis placement matters.** Contour points define the Z=0 side (left side, X=0). After extrusion, the part spans from X=0 to X=thickness. Center the final model: translate X by -thickness/2 after joining.

5. **Boolean UNION not needed for weapon profiles.** Joining (`bpy.ops.object.join()`) is sufficient for weapon models where parts sit adjacent rather than overlapping deeply. Boolean UNION is slow and unnecessary here.
