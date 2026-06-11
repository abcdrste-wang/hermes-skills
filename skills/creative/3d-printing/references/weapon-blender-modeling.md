# Weapon Model Case Study: 无境空刃 (FFAR1 Mythic Skin)

## Background
User (小蓝, 8-year-old child) asked for an STL model of the 无境空刃 — the FFAR1 Mythic weapon skin from Call of Duty Mobile.

## Initial Failure
I chose numpy-stl box composition (长方体拼接法), producing 4 iterations:
- v1: 868 faces, 108mm — basic cylinder+box, unrecognizable
- v2: 1196 faces — grid-based voxel approximation, still blocky
- v3: cylinder/cone composite, buggy dimension alignment
- v4: 1068 faces, 72.8mm×7.3mm×8.6mm — all flat boxes

**User reaction**: "你这stl 做的啥啊，完全看不出枪的样子，好好反省一下"

## Root Cause
I chose the wrong tool. Blender was already installed at `/Applications/Blender.app/` but I never checked. numpy-stl cannot produce recognizable weapon shapes — it can only do blocky approximations.

## Correct Approach
Switched to Blender Python API (bpy) headless mode:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python blender_wujing.py
```
Result: 611 faces, 100mm long, with cylindrical barrel, cone muzzle, grooved handguard, angled grip, textured magazine, and detailed stock.

## Case Study 2: CF-007 Assault Rifle (CODM)

### Background
After 无境空刃, the user's child (瑞瑞, 8yo) requested a 3D model of the CF-007 assault rifle from CODM. User/瑞瑞 wanted a printed physical model for decoration.

### Approach: Blender direct mesh data manipulation (no modifiers)

Unlike 无境空刃 which used Blender `bpy.ops.mesh.primitive_*` + boolean UNION, CF-007 used **pure bmesh direct mesh construction** — no modifiers at all. This was a deliberate choice after discovering that Blender background mode does NOT reliably apply modifiers like Mirror, Boolean, or Subdivision Surface when using `bpy.ops.object.modifier_apply()` — the call succeeds silently but the mesh remains unchanged.

**Why modifiers failed in background mode:**
- `bpy.ops.object.modifier_apply(modifier='Mirror')` runs without error but mesh doesn't change
- `mod.solver = 'FAST'` removed in 5.x (use `'FLOAT'`)
- `mod.use_axis[0] = True` is correct API but apply still fails in headless
- Result with Mirror: exported STL had only the base mesh (e.g. 102 faces vs expected 2000+)

**The fix: Build symmetry manually instead of relying on Mirror modifier. Use bmesh to construct ALL geometry directly, then JOIN objects, then export STL — no modifier apply step at all.**

```python
# Pattern: build_each_part_as_bmesh → create mesh objects → JOIN → export

import bpy, bmesh, math

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
```

### Results
- **CF-007 rifle**: 366KB, 3744 faces, 120mm long — recognizably a weapon
- Key difference from 无境空刃: used direct mesh data + mirror-symmetry by hand (no modifier dependency)

### Blender Background Render Pitfall: Side View Goes Black

When rendering weapon model previews in background mode, the side view may render as **completely black** even when front and isometric views work fine. This happens because of camera direction and the `TRACK_TO` constraint:

**Symptoms:**
- Front view (camera at positive Y, looking at origin): ✅ renders fine
- Side view (camera at positive X, looking at origin): ❌ renders all black
- Scene camera is set properly
- Lights are in place and working (front/iso views confirm this)

**Root Cause:**
The `TRACK_TO` constraint (`bpy.ops.object.constraint_add(type='TRACK_TO')`) does NOT work reliably in headless background mode — it may not orient the camera toward the target. The camera ends up pointing in its default direction (usually down -Z), which may face away from the model.

**Fix: Set camera rotation Euler directly instead of using constraints:**

```python
import math

# For front view (looking along -Y axis):
bpy.ops.object.camera_add(location=(0, -8, 3))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(70), 0, 0)  # Pitch up 70° to look at origin from Y=-8

# For side view (looking along -X axis):
bpy.ops.object.camera_add(location=(8, 0, 3))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(70), 0, math.radians(90))  # +90° yaw = point along -X

# For top view (looking down -Z):
bpy.ops.object.camera_add(location=(0, 0, 10))
cam = bpy.context.active_object
cam.rotation_euler = (0, 0, 0)  # Default camera looks down -Z
```

**Alternative (mathutils approach, more precise):**
```python
import mathutils

def point_camera_at(cam_obj, target=(0, 0, 0)):
    direction = mathutils.Vector(target) - cam_obj.location
    # No need for TRACK_TO — just set rotation directly
    quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = quat.to_euler()
```

**Verification:** After rendering, check pixel brightness of the output file:
```bash
python3 -c "
from PIL import Image; import numpy as np
img = Image.open('render.jpg').convert('L')
arr = np.array(img)
print(f'Mean brightness: {arr.mean():.1f}')
if arr.mean() < 30: print('ALL BLACK - fix camera direction')
"
```

## Key Lessons

### Tool Selection (CRITICAL)
| Scenario | Tool | Why |
|----------|------|-----|
| Weapon/mecha model | **Blender** | Curved barrels, conical parts, angled grips |
| Organic character | **Blender** | Subdivision surfaces for smooth contours |
| Simple box/phone case | **numpy-stl** | 5-second generation, no Blender startup |
| Anything user says "看不出样子" | **Blender** | Immediately switch; don't iterate numpy-stl |

### Blender 5.1 STL Export API Fix
In Blender 5.x, `bpy.ops.wm.stl_export()` uses:
```python
bpy.ops.wm.stl_export(
    filepath=OUTPUT,
    export_selected_objects=True,  # NOT 'use_selection' (removed in 5.x)
    ascii_format=False,
    global_scale=1.0
)
```

### Weapon Modeling Strategy
Build from individual primitives placed at (cx, cy, cz) coordinates along Y-axis:
1. **Barrel** (Y=2.0 to 4.0): Cylinder + cone muzzle tip + flared ring
2. **Handguard** (Y=1.0 to 2.8): Box with top/bottom rails + side grooves
3. **Receiver** (Y=-0.3 to 1.2): Main box + ejection port + panel lines
4. **Grip** (Y=-0.8 to 0.0): Stepped boxes with Y-tilt for angled grip
5. **Magazine** (Y=-0.9 to -0.3): Box with grid texture detail
6. **Stock** (Y=-2.2 to -0.4): Box with frame rails + grooves
7. **Sights**: Small boxes at receiver (rear) and barrel (front)

Rotation convention: Y = barrel direction, X = width, Z = height

### 🔬 Mandatory: Quality self-check before sending to user

**User's rule (non-negotiable):** Before sending any model to the user, you MUST perform a strict self-check comparing the reference image(s) against the actual STL — "是不是一个东西？是不是一个档次的东西？先过你自己这一关，然后再考虑发不发。"

**当GLM视觉模型描述模糊时的处理（如只说"流线型""复杂几何"而没有具体几何特征）：**
- 不要依赖单张vision_analyze描述来建模——多角度独立分析至少3-4张参考图
- 对每个部件问具体问题（"枪口制退器有几条开槽？枪托是实心还是骨架式？弹匣形状？"）
- 如果视觉模型说"无法确定"，在建模脚本中显式标注哪些部件有参考依据、哪些是推测
- 三角面数不足(＜3000面)的模型无法呈现游戏级武器细节

### Checklist for Weapon Models (Updated with FFAR1 lessons)
- [ ] Check if Blender is installed BEFORE writing any code
- [ ] Collect 2+ reference images (Bilibili 4K display videos are best)
- [ ] **Self-check BEFORE modeling**: Analyze each reference image individually. For each part (barrel, handguard, receiver, grip, magazine, stock, sights, muzzle device, trigger guard), write down specific geometric observations. Do NOT rely on a single vision_analyze call for modeling decisions.
- [ ] **Decide modeling approach**:
  - **Modifier approach** (bpy.ops.mesh.primitive + boolean UNION + Mirror): Use only when you've verified modifier_apply works in this Blender version. Test with a simple 2-part boolean union first.
  - **Direct mesh approach** (bmesh from_pydata, no modifiers): Preferred for weapons — build each half manually, create symmetric parts by duplicating and flipping, no modifier apply needed. More lines of code but ALWAYS works.
- [ ] Model barrel as cylinder (not box approximation)
- [ ] Add muzzle cone/ring for visual recognition
- [ ] Grip needs angle/tilt (not straight block)
- [ ] Magazine needs some texture (grid lines or ridges)
- [ ] Add trigger guard
- [ ] Stock: is it solid or skeleton/framework? If skeleton, model support bars explicitly
- [ ] Sights: add front+rear sights
- [ ] STL export: use `export_selected_objects=True` in Blender 5.x (NOT `use_selection`)
- [ ] **Check triangle count**: <1000面 = 只能做粗放形状，细节不可见。游戏武器模型建议3000-5000面起步。
- [ ] Verify STL vertex bounds after generation (>2mm on all axes, Z centroid > 0)
- [ ] **Render verification**:
  - Front view: camera at (0, -distance*1.5, height), rotation_euler=(pitch_degrees, 0, 0)
  - Side view: camera at (distance, 0, height), rotation_euler=(pitch_degrees, 0, 90°)
  - Top view: camera at (0, 0, distance), rotation_euler=(0, 0, 0)
  - Check rendered pixel brightness — if all black, fix camera rotation directly (no TRACK_TO constraint)
- [ ] Send STL + rendered preview to user before finalizing

---

### Related reference: Modifier apply failure in headless mode

See `references/blender-modifier-headless-pitfall.md` for the full case study on why `bpy.ops.object.modifier_apply()` silently fails in Blender background mode, and the direct bmesh workaround discovered during CF-007 modeling. TL;DR: Never rely on modifier apply in `--background` mode — build geometry directly with bmesh.
