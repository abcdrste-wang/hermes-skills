# STL Editing Workflow Case Study: FFAR1 无境空刃 (2026-06-08)

## Background

User had a Bambu AI-generated STL model (500K faces, 100×28×8mm bounding box) of a CODM weapon skin. They wanted 3 modifications:
1. **Gun barrel**: 3 muzzle openings → 1 (single round hole)
2. **Scope**: tall sharp point → low profile with 2 ridges ("耳朵")
3. **Glow effect**: render an orange glowing disc in the center (STL addition, not just render)

## Key Challenges Discovered

### 1. "Editing existing STL" ≠ "Modeling from scratch"

The skill's entire workflow assumes building new geometry. Editing an existing 500K-face STL requires a completely different approach:
- You don't know the model's topology — each vertex has a purpose
- Deleting a vertex region leaves a gaping hole that must be filled
- Adding new parts means topological merge, not boolean operations

### 2. Headless modifier apply fails silently — again

Confirmed for the 3rd time: SUBSURF, MIRROR, BOOLEAN, BEVEL all fail when using `bpy.ops.object.modifier_apply()` in `blender --background` mode. The fix: use bmesh direct operations exclusively.

### 3. Bisect direction is easy to get wrong

```python
# RIGHT direction for FFAR1 barrel cut (Y=50 is muzzle end, Y=-50 is stock end):
bmesh.ops.bisect_plane(bm, geom=..., plane_co=(0, 49, 0), plane_no=(0, 1, 0), clear_inner=True)
```
- `clear_inner=True` = delete Y>49 (muzzle tip)
- `clear_outer=True` = delete Y<49 (keep only muzzle tip)

The first attempt used the wrong direction — deleted the entire body instead of just the muzzle.

### 4. Volume check catches problems user won't see

After bisect the wrong way: 5,182 mm³ → 105 mm³. This is a sure sign the edit cut the wrong side.

### 5. Face count verification

After deleting muzzle end, face count should stay roughly the same. v5 correctly kept ~500K faces.
When grid_fill fails: face count may drop dramatically (e.g., 500K → 8K).

## Procedure That Worked (v5)

```
1. Import STL
2. Enter EDIT mode, get bmesh from_edit_mesh
3. Select vertices to delete (Y > 49)
4. bmesh.ops.delete with context='VERTS'
5. Find open edges (1 link_face only)
6. grid_fill with those edges, use_smooth=True
7. Add new parts as separate primitives
8. Join all with bpy.ops.object.join()
9. Export STL
10. Check face count, volume, bounding box via trimesh
```

## Key Numbers

| Metric | Original | After edit (v5) | Notes |
|--------|----------|-----------------|-------|
| Face count | 500K+ | 500K+ | Good — no collapse |
| Volume | 5,182 mm³ | 4,830 mm³ | ~7% reduction from removing muzzle tip — reasonable |
| Y range | -50 to 50 | -50 to 49 | Muzzle tip removed cleanly |
| Z max | 14.2 mm | 14.2 mm | Scope height unchanged (separate edit) |

## Render Failure (M4 EEVEE headless — 3rd confirmation)

EEVEE headless renders on Mac Mini M4 (16GB, no dedicated GPU) produced uniformly flat gray images twice in this session. Must use `stl_2d_preview.py` with 2D line-art projection for structural verification. EEVEE is only usable for the final "color" render but will always look washed out.
