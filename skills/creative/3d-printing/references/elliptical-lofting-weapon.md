# Elliptical Cross-Section Lofting for Weapon/Energy Blade Models

> **Source**: FFAR1「无境空刃」CODM mythic weapon skin, modeled 2026-06-09
> **Paradigm**: Elliptical cross-section stacking = true 3D depth for tube-like objects

## Problem Solved

Side-profile extrusion produces a flat/stamp-like result (thin slice, no 3D depth). Box composition produces blocky unrecognizable shapes. **Elliptical cross-section stacking** produces real 3D volume with varying thickness along the length — the correct paradigm for weapons, energy blades, and any tube-like organic form.

## Core Concept

Instead of extruding a contour → thin slice, build the model by stacking different-sized elliptical cross-sections along the object's length:

```
Cross-section at any point on the weapon:
  - semi-major axis (half-width, W/2) — horizontal extent
  - semi-minor axis (half-thickness, T/2) — depth extent
  
The ratio W:T defines local shape:
  W ≈ T → circular (barrel section)
  W > T → flat oval (blade section)
  W ≪ T → tall oval (vertical fin)
```

## Algorithm

```python
import numpy as np, math, struct

def build_weapon_loft(sections, output_stl):
    """
    sections: list of (z, width, thickness, segments)
    Each section at depth z has a horizontal width and vertical thickness.
    Uses 2N vertices per section (mirrored pairs).
    """
    segs = 16  # default
    verts = []  # vertices list
    tris = []   # triangle faces
    
    for i, (z, w, t) in enumerate(sections):
        # Generate top half (positive side of ellipse)
        for j in range(segs + 1):
            angle = math.pi * j / segs  # 0 to π (top half)
            x = (w / 2) * math.cos(angle)
            y = z  # Z = long axis
            z_coord = (t / 2) * math.sin(angle)
            verts.append((x, y, z_coord, i, j))  # section_index, segment_index
    
    # Bottom half: mirror top half's X and Z
    # (or generate separately for asymmetric profiles)
    
    # Build faces between consecutive sections
    for i in range(len(sections) - 1):
        for j in range(segs):
            a = i * (segs + 1) + j
            b = a + 1
            c = (i + 1) * (segs + 1) + j
            d = c + 1
            tris.append((a, b, c))
            tris.append((b, d, c))
    
    # Write binary STL
    # ... standard binary STL export
```

## Parameter Design Pattern

Rather than defining every section manually, use **piecewise functions** that describe how width and thickness vary along the weapon:

```python
# Example: FFAR1 "无境空刃"
# Z axis runs from 0 (grip tip) to weapon_length (muzzle tip)
L = 140.0  # total length mm

def width_at(z):
    """Horizontal width at depth z along the weapon"""
    ratio = z / L
    
    if ratio < 0.05:      # grip end
        return 2 + ratio * 60
    elif ratio < 0.10:     # grip → body transition
        return 5 + (ratio - 0.05) * 200
    elif ratio < 0.20:     # lower body
        return 15
    elif ratio < 0.25:     # waist dip (narrow waist)
        return 15 - (ratio - 0.20) * 100
    elif ratio < 0.40:     # main body
        return 10 + (ratio - 0.25) * 33
    elif ratio < 0.65:     # upper body, expanding to disc area
        return 15 + (ratio - 0.40) * 40
    elif ratio < 0.70:     # disc region (widest point)
        return 25 + (ratio - 0.65) * 100
    elif ratio < 0.80:     # taper after disc
        return 30 - (ratio - 0.70) * 100
    elif ratio < 0.95:     # muzzle shaft
        return 20 - (ratio - 0.80) * 67
    else:                  # muzzle tip
        return 10 - (ratio - 0.95) * 100

def thickness_at(z):
    """Vertical thickness (depth) at depth z"""
    ratio = z / L
    
    if ratio < 0.05:
        return 2 + ratio * 60
    elif ratio < 0.10:
        return 5 + (ratio - 0.05) * 200
    elif ratio < 0.20:
        return 15
    elif ratio < 0.25:
        return 15 - (ratio - 0.20) * 100
    elif ratio < 0.40:
        return 10 + (ratio - 0.25) * 33
    elif ratio < 0.65:
        return 15 + (ratio - 0.40) * 20
    elif ratio < 0.70:
        return 17 + (ratio - 0.65) * 40
    elif ratio < 0.80:
        return 19 - (ratio - 0.70) * 40
    elif ratio < 0.95:
        return 15 - (ratio - 0.80) * 33
    else:
        return 10 - (ratio - 0.95) * 100
```

## Adding Detail Features via Cross-Section Manipulation

Instead of adding features as separate parts (which needs boolean UNION), encode them as **local cross-section distortions**:

### 1. Elliptical Holes (Waist Holes / Side Vents)

```python
def add_side_holes(verts, tris, hole_center_z, hole_width, hole_height, hole_count=2, segs=16):
    """
    Remove triangles in the elliptical hole region at a specific depth.
    Works by marking those triangles as 'removed' (not adding to final list).
    """
    new_tris = []
    for tri in tris:
        tri_verts = [verts[i] for i in tri]
        tri_center_z = sum(v[1] for v in tri_vert_zs) / 3
        tri_center_x = sum(v[0] for v in tri_vert_xs) / 3
        
        if abs(tri_center_z - hole_center_z) < hole_height / 2:
            # Check if within elliptical hole region
            dx = abs(tri_center_x)  # symmetric on both sides
            dz = abs(tri_center_z - hole_center_z)
            if (dx / (hole_width/2))**2 + (dz / (hole_height/2))**2 <= 1:
                continue  # skip — this triangle is inside the hole
        new_tris.append(tri)
    return new_tris
```

### 2. Wing-Like Fork Structures (Side Protrusions)

```python
def add_fork_protrusions(verts, tris, fork_start_z, fork_end_z, fork_max_width, segs=16):
    """
    Warp the elliptical cross-section to extend laterally in a fork-like shape.
    Instead of a smooth ellipse, the cross-section has two wing-like extensions.
    """
    new_verts = list(verts)
    new_tris = []
    
    for i, section_i in enumerate(section_indices):
        z = section_zs[i]
        ratio = (z - fork_start_z) / (fork_end_z - fork_start_z)
        if 0 <= ratio <= 1:
            wing_width = fork_max_width * math.sin(ratio * math.pi)
            # For each vertex at this section, add wing extension
            # At angle 0 and π (far left/right), extend outward
            # ...
    
    return new_verts, new_tris
```

### 3. Scope / Mid-body Glow Disc

Add as a localized cylinder ring around the main body:

```python
def add_glow_disc(sections, disc_center_z, disc_width, disc_thickness, segs=32):
    """
    Add a disc-shaped protrusion around the main body at disc_center_z.
    """
    disc_sections = [
        (disc_center_z - disc_width/2, body_width, body_thickness),
        (disc_center_z, disc_radius * 2, disc_thickness),
        (disc_center_z + disc_width/2, body_width, body_thickness),
    ]
    # Merge into existing section list, sorted by z
    merged = sorted(sections + disc_sections, key=lambda s: s[0])
    return merged
```

## Paradigm Comparison Summary

| Approach | 3D Depth | Recognizable | Manual Work | Best For |
|----------|----------|-------------|-------------|----------|
| Box composition | ★☆☆ (flat) | ★☆☆ (blocky) | Low | Geometric objects |
| Side-profile extrusion | ★★☆ (thin stamp) | ★★★☆ (silhouette) | Medium | Flat objects, coins |
| **Elliptical lofting** | **★★★★ (full volume)** | **★★★★☆** | **Medium-High** | **Weapons, energy blades, handles** |
| Boolean-composite (separate parts) | ★★★★ | ★★★★ | High | Multi-material prints |

## Key Lessons

1. **The width and thickness functions are the design** — getting these curves right determines 90% of the outcome. Iterate on the piecewise functions, not on vertex counts.

2. **36-40 sections × 16-24 segments** produces ~1000-2000 faces — sufficient for preview. Final version can target 3000-5000 faces for smooth curves.

3. **Segments = 24** minimum for visibly smooth curves (16 segments shows faceting on close inspection).

4. **Do NOT use numpy-stl for this** — the algorithm is simple enough to write yourself, and controlling vertex-to-face mapping is easier with raw Python + struct.

5. **Render verification**: When EEVEE on M4 produces flat gray images, use 2D side-view projection instead — even raw vertex xz-coordinates drawn with Pillow show the silhouette clearly.
