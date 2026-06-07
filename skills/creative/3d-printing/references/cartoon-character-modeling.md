# Cartoon Character Modeling for One-Piece 3D Printing

## When to use this

User wants a **3D-printable cartoon character**: an animal, mascot, action figure, or toy. The models must look like the thing they represent — not "6个椭圆形" (six ellipsoids), which was the user's exact complaint about a first-pass TMNT Turtle model.

## Golden rule: Research references BEFORE modeling

**NEVER start modeling a cartoon character without first researching its visual references.** This was learned the hard way after a TMNT Turtle was rejected for having "no connection between parts, no eyes, no nose, no tail, no nails" — because no reference was checked.

Workflow:
1. If the user says "design a Ninja Turtle" or similar character, **first search the web** for reference images/descriptions of that character
2. Identify specific visual features: eye shape, shell ridges, mask color, finger/toe count, tail type
3. Note the proportions: head-to-body ratio, limb thickness, shell shape
4. Write down the feature list before writing any modeling code

> If behind GFW and web search is blocked, ask the user if a proxy is available (e.g. V2rayU on `127.0.0.1:1087`) before proceeding blind.

## Core principle: Each body part needs its OWN recognizable shape

The fatal mistake: building all body parts as **spheres/ellipsoids of different sizes**. A sphere head + sphere body + sphere legs = "six ellipsoids" even after boolean union.

Instead, each part must be built with geometry that makes it look like what it represents:

| Body Part | Wrong approach | Right approach |
|-----------|---------------|----------------|
| Head | Simple sphere | Sphere + jaw extension + cheek bulges + brow ridge |
| Eyes | One sphere per eye | White sclera sphere + smaller black pupil sphere |
| Nose | Tiny sphere | Cone/ellipsoid protruding visibly from face |
| Mouth | Thin cylinder | Beveled box or curved extruded shape for smile |
| Shell | Single dome ellipsoid | Dome + 2-3 raised ridge lines (elongated ellipsoids) |
| Arms | Cylinder/ellipsoid | Segmented: upper arm + forearm + hand + fingers |
| Legs | Single tapering cone | Thigh + calf + foot + separated toes |
| Hands | Single sphere | Palm box + 4-5 individual cylindrical fingers |
| Feet | Single ellipsoid | Foot pad + 3-4 individual toes with rounded tips |
| Tail | Long cone | Tapering curved ellipsoid (thicker at body, thinner at tip) |
| Mask/bandana | Flat plane | Head-conforming band + trailing streamers behind head |

## Part inventory: TMNT Turtle example

A complete TMNT-style turtle needs these 25+ parts for acceptable detail:

```
Turtle body parts (minimal viable set):
├── Shell (dome ellipsoid, large)
├── Shell ridge 1 (center, elongated)
├── Shell ridge 2 (left)
├── Shell ridge 3 (right)
├── Head (large sphere)
├── Neck (smaller sphere bridging head ↔ body)
├── Eye mask band (toroidal/arc around eyes)
├── Mask streamer left (flat ribbon trailing back)
├── Mask streamer right (flat ribbon trailing back)
├── Eye white left (small sphere)
├── Eye white right (small sphere)
├── Pupil left (tiny sphere)
├── Pupil right (tiny sphere)
├── Nose (small ellipsoid, protruding)
├── Mouth (arc-shaped extrusion)
├── Arm left (thick cylinder/ellipsoid)
├── Arm right (thick cylinder/ellipsoid)
├── Hand left (box, wider at end)
├── Hand right (box, wider at end)
├── Fingers × 5 (thin cylinders on each hand)
├── Fingernail × 5 (tiny spheres on each finger tip)
├── Leg left (thick ellipsoid)
├── Leg right (thick ellipsoid)
├── Foot left (box)
├── Foot right (box)
├── Toes × 3-4 (small ellipsoids on each foot)
├── Toenail × 3-4 (tiny spheres on each toe tip)
└── Tail (elongated cone/ellipsoid, rear center)
```

### Naming convention

Use snake_case or CamelCase for part names — makes debugging easier:
```python
parts = {
    'shell': make_dome(...),
    'shell_ridge_1': make_ellipsoid(...),
    'head': make_sphere(...),
    'neck': make_sphere(...),
    'eye_white_L': make_sphere(...),
    'eye_pupil_L': make_sphere(...),
    # ... 25+ parts total
}
```

## Building recognizable features in Blender

### Shell with ridges (TMNT-style)

```python
def make_shell(radius_x=30, radius_y=35, radius_z=20, segs=32):
    """Domed turtle shell — bottom is flattened, top is domed"""
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=1, segments=segs, ring_count=segs//2,
        location=(0, 0, 0)
    )
    obj = bpy.context.object
    obj.name = "Shell"
    obj.scale = (radius_x, radius_y, radius_z)
    bpy.ops.object.transform_apply(scale=True)
    
    # Bisect off bottom half to make it a dome
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, 0, -radius_z * 0.3),  # cut at ~30% from bottom
        plane_no=(0, 0, 1),
        clear_inner=True,    # remove bottom
        clear_outer=False
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj

def add_shell_ridges(body, cx=0, cy=0, shell_z=0, ridge_len=40, ridge_radius=5):
    """Add 3 raised ridges to shell dome"""
    for i, (dx, dz_offset) in enumerate([(0, 0.2), (-12, 0.1), (12, 0.1)]):
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=1, segments=16, ring_count=8,
            location=(cx + dx, cy, shell_z + ridge_radius * 0.5)
        )
        ridge = bpy.context.object
        ridge.name = f"ShellRidge_{i}"
        ridge.scale = (ridge_radius, ridge_len, ridge_radius * 0.6)
        bpy.ops.object.transform_apply(scale=True)
        
        # Tilt slightly toward shell center for natural look
        ridge.rotation_euler = (0.15 * dx/12, 0, 0)
        
        boolean_union(body, ridge)
```

### Eyes (recognizable look)

```python
def add_eyes(body, cx=0, face_y, face_z, head_radius=16):
    """Add recognizable eyes: white sclera + black pupil"""
    eye_offset = 6  # distance from center
    for side, sign in [("L", -1), ("R", 1)]:
        # White of eye
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=head_radius * 0.22, segments=16, ring_count=12,
            location=(cx + sign * eye_offset, face_y + head_radius * 0.5, face_z + head_radius * 0.15)
        )
        white = bpy.context.object
        white.name = f"EyeWhite_{side}"
        boolean_union(body, white)
        
        # Pupil (smaller, on top of white)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=head_radius * 0.1, segments=12, ring_count=8,
            location=(cx + sign * eye_offset, face_y + head_radius * 0.55, face_z + head_radius * 0.2)
        )
        pupil = bpy.context.object
        pupil.name = f"EyePupil_{side}"
        boolean_union(body, pupil)
```

### Mouth (smile)

```python
def add_mouth(body, cx=0, face_y, face_z, head_radius=16):
    """Add a curved smile using a beveled box"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, face_y + head_radius * 0.2, face_z - head_radius * 0.3))
    mouth = bpy.context.object
    mouth.name = "Mouth"
    mw = head_radius * 0.4  # mouth width
    mh = head_radius * 0.1  # mouth height
    mouth.scale = (mw, mh, mh * 0.5)
    bpy.ops.object.transform_apply(scale=True)
    # Tilt into a smile arc
    mouth.rotation_euler = (0.2, 0, 0)  # slight upward curve at ends
    boolean_union(body, mouth)
```

### Fingers and toes (individual + nails)

```python
def add_fingers(body, hand_center, hand_width, count=5):
    """Add individual fingers with nail spheres at tips"""
    for i in range(count):
        x = hand_center[0] + (i - count/2 + 0.5) * (hand_width * 0.8 / count)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.6, depth=4, 
            location=(x, hand_center[1] + 2, hand_center[2]),
            rotation=(math.radians(90), 0, 0)
        )
        finger = bpy.context.object
        finger.name = f"Finger_{i}"
        boolean_union(body, finger)
        
        # Nail at tip
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.4, segments=8, ring_count=6,
            location=(x, hand_center[1] + 5, hand_center[2])
        )
        nail = bpy.context.object
        nail.name = f"Nail_{i}"
        boolean_union(body, nail)
```

### Mask/bandana (TMNT-style)

```python
def add_mask(body, cx=0, face_y, face_z, head_radius=16):
    """Add eye mask band (wrapping around eyes + trailing streamers)"""
    # Mask band: torus/annulus wrapping around eye area
    bpy.ops.mesh.primitive_torus_add(
        major_radius=head_radius * 0.4,
        minor_radius=head_radius * 0.08,
        location=(cx, face_y + head_radius * 0.1, face_z + head_radius * 0.1),
        rotation=(0, math.radians(90), 0)
    )
    mask = bpy.context.object
    mask.name = "MaskBand"
    mask.scale = (1, 1, 1.5)  # stretch laterally
    bpy.ops.object.transform_apply(scale=True)
    boolean_union(body, mask)
    
    # Streamers (tail behind head)
    for side, sign in [("L", -1), ("R", 1)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(
            cx + sign * head_radius * 0.6,
            face_y - head_radius * 0.5,
            face_z + head_radius * 0.1
        ))
        streamer = bpy.context.object
        streamer.name = f"MaskStreamer_{side}"
        streamer.scale = (head_radius * 0.3, head_radius * 0.5, head_radius * 0.05)
        bpy.ops.object.transform_apply(scale=True)
        # Angle outward
        streamer.rotation_euler = (0, 0, sign * 0.3)
        boolean_union(body, streamer)
```

## Verification checklist

After generating the STL, run this BEFORE sending to user:

```bash
python3 -c "
import numpy as np
with open('TMNT_Turtle.stl', 'rb') as f:
    d = f.read()
nt = int.from_bytes(d[80:84], 'little')
verts = []
for i in range(nt):
    for j in range(3):
        v = np.frombuffer(d[84+i*50+12+j*12:84+i*50+24+j*12], dtype=np.float32)
        verts.append(v)
verts = np.array(verts)
rng = [verts[:,i].max()-verts[:,i].min() for i in range(3)]
print(f'Triangles: {nt}')
print(f'Size:   {rng[0]:.1f} x {rng[1]:.1f} x {rng[2]:.1f} mm')
print(f'Z:      {verts[:,2].min():.2f} ~ {verts[:,2].max():.2f}')
low_z = verts[verts[:,2] < 3]
flat_z = len(np.unique(np.round(low_z[:,2], 6)))
print(f'Bottom flatness: Z<3mm vertices: {len(low_z)} unique Z values: {flat_z}')
if flat_z == 1:
    print('  ✅ Bottom is flat')
else:
    print('  ⚠️  Bottom has multiple Z levels — may need supports!')
if nt > 2000:
    print('  ✅ Sufficient detail')
elif nt > 500:
    print('  ⚠️  Low detail — may look faceted')
else:
    print('  ❌ Too few triangles — model is too simple!')
"
```

## Render preview strategy for cartoon models

Use **Cycles** (not EEVEE) for headless rendering of cartoon character models — Cycles handles the materials and lighting better without the EEVEE attribute removal issues in Blender 5.x:

```python
def setup_cycles_render(scene):
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.cycles.samples = 32  # low for preview; 128+ for final
    scene.render.film_transparent = False
    
    # Light world background
    world = scene.world
    if not world.use_nodes:
        world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1.0)

def assign_tmnt_material(obj, color=(0.1, 0.7, 0.15, 1.0), roughness=0.3):
    """Bright green for TMNT skin; adjust color per character."""
    mat = bpy.data.materials.new(f"Mat_{obj.name}")
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get('Principled BSDF')
    if principled:
        principled.inputs['Base Color'].default_value = color
        principled.inputs['Roughness'].default_value = roughness
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
```

Cycles at 32 samples + Apple Silicon M4 renders a 1200×1200 preview in ~25-35 seconds with good visibility. EEVEE is faster (~3s) but more fragile in headless mode on Blender 5.x.

## If model is rejected as "too simple"

This exact feedback pattern occurred in the TMNT session:
- User said "只有6个椭圆形" (only 6 ellipsoids)
- User said "没有连接" (no connection between parts)
- User said "眼睛鼻子尾巴指甲都没有" (no eyes, nose, tail, nails)

If the user says any of these, the fix is NOT to tweak scales — the fix is to **add more distinct body parts**. Add fingers, add nails, add a nose, add a proper mouth, add an eye mask, add shell ridges. The issue isn't that the spheres are the wrong size — it's that there aren't enough of them in the right places to form recognizable features.
