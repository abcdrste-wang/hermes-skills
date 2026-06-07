# Articulated Cat — 3D Printable Toy (Reference Implementation)

Generated for user on 2026-06-06. Two versions produced: a **numpy-stl basic version** and a **Blender sculpted version**. This file documents both.

## Version 1: numpy-stl (basic)

Generated with Python + numpy-stl. Faceted but functional.

## Design dimensions

```
GAP = 0.4mm  (standard 0.4mm nozzle width — print ready, no post-processing)
```

### Part dimensions (mm)

| Part | Shape | Size |
|------|-------|------|
| Body | Ellipsoid (stretched sphere) | 27×18×16 |
| Head | Sphere | R=12 |
| Ears (×2) | Cone (6→1mm taper) | H=8 |
| Front legs (×2) | Cylinder | R=4, H=14 |
| Rear legs (×2) | Cylinder | R=4.5, H=16 |
| Tail | 3-segment tapered cylinder | R=3→1, total L=20 |

### Assembled size: 55mm tall × 65mm long × 20mm wide

## File structure

```
~/.hermes/3d_models/
├── cat_preview.py            # Generator script
├── cat_preview.png           # 2D preview (front/side/top views + metadata)
├── cat_body.stl              # Body
├── cat_head.stl              # Head + ears (merged)
├── cat_front_left.stl        # Left front leg
├── cat_front_right.stl       # Right front leg
├── cat_rear_left.stl         # Left rear leg
├── cat_rear_right.stl        # Right rear leg
├── cat_tail.stl              # Tail
└── cat_assembled.stl         # Full assembly (reference only)
```

## Key technique: joint articulation

The legs use a **simple cylinder joint** pattern:
1. Leg is a cylinder with a flat top
2. Body has a corresponding cylindrical socket
3. Gap of 0.4mm between peg and socket
4. After printing, press-fit the leg cylinder into the body socket
5. The leg swings forward/backward around the cylindrical axis

For the **head joint**:
1. Head base is a flat-bottomed sphere
2. Body has a concave socket at the front
3. Head sits in socket and rotates freely

## Print instructions delivered to user

```
材料：PLA / PETG
层高：0.2mm
支撑：不需要
喷嘴：0.4mm
填充：15-20%
```

## Customization guide

To generate a different animal (dog, rabbit, bear):
1. Change `BODY_LX/LY/LZ` for proportions
2. Change `HEAD_R` for head size
3. Change `LEG_R/LEG_H` for limb size
4. Change `EAR_BASE/EAR_HEIGHT` and ear position for different ear shapes
5. Adjust `LEG_GAP_X` / `FRONT_LEG_Y` / `REAR_LEG_Y` for stance width

To generate a simpler single-piece model (keychain, fidget toy, badge):
1. Merge all parts into one STL
2. Skip the joint gaps
3. Remove rotation helpers

## Source code location

### Version 1: numpy-stl
Full generator script: `~/.hermes/3d_models/cat_preview.py` (444 lines)
Pattern: build geometry helpers → compose parts → export STLs → generate preview

## Version 2: Blender (smooth, organic)

Generated with `blender --background --python blender_cat_gen.py`. Uses subdivision surfaces, Bezier curve tail, EEVEE render preview.

### Blender file location

- Script: `~/.hermes/3d_models/blender_cat_gen.py` (~260 lines)
- Render script: `~/.hermes/3d_models/render_preview.py`
- Output: `~/.hermes/3d_models/blender_cat/`
- Blender API quirks documented in `references/blender-5.1-api.md`
