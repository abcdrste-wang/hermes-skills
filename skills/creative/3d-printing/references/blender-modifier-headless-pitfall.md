# Blender Headless Mode: Modifier Apply Failure

## Discovery
During CF-007 assault rifle modeling (2026-06-08), `bpy.ops.object.modifier_apply()` was found to silently fail in Blender background mode (`--background`).

## Symptoms
- Mirror modifier applied → only base half exported (102 faces instead of 204)
- Boolean UNION modifier applied → objects remain separate in exported STL
- Subdivision Surface modifier applied → exported mesh shows un-subdivided base mesh
- **No error message** — `modifier_apply()` returns successfully, but mesh data is unchanged

## Affected Modifier Types
All modifier types have been observed to fail:
- `MIRROR` — base half only
- `BOOLEAN` — no boolean operation applied
- `SUBSURF` — no subdivision
- `ARRAY` — array not applied
- `BEVEL` — no bevel applied

## Root Cause (Hypothesis)
In background mode, Blender does not fully evaluate the dependency graph before the apply operation. The modifier is "applied" logically (the modifier stack entry is removed) but the underlying mesh data was never evaluated from the modifier's output.

## Reliable Workaround: Direct Mesh Construction

**Build symmetry manually instead of using Mirror modifier:**

```python
def build_symmetric(right_verts, right_faces):
    \"\"\"Build symmetric mesh without Mirror modifier\"\"\"
    all_verts = list(right_verts)
    all_faces = list(right_faces)
    n = len(right_verts)
    for v in right_verts:
        all_verts.append((-v[0], v[1], v[2]))
    for face in right_faces:
        all_faces.append(tuple(n + i for i in reversed(face)))
    return all_verts, all_faces
```

**Use bmesh.from_pydata() for all geometry construction:**

```python
import bpy, bmesh

def create_mesh_obj(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(list(verts), [], list(faces))
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj
```

**For JOIN operation (combining parts):**

```python
# Select all parts and join
bpy.ops.object.select_all(action='DESELECT')
for part in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()

# For STL export, use:
bpy.ops.wm.stl_export(
    filepath=OUTPUT,
    export_selected_objects=True,
    ascii_format=False,
    global_scale=1.0
)
```

## When to Even Try Modifiers

Only use modifiers in headless mode when:
1. You have tested modifier_apply with a SIMPLE 2-object test case in the SAME Blender version
2. You can verify the result (check triangle count before and after)
3. You have a fallback to the direct mesh approach if it fails

## Verification After Any Modifier Apply

```python
# Always check face count before vs after
print(f"Before: {len(obj.data.polygons)} faces")
bpy.ops.object.modifier_apply(modifier=mod.name)
# Re-read the mesh data
print(f"After: {len(obj.data.polygons)} faces")
# If counts are equal, modifier did NOT apply!
```

## Case Study: CF-007 Rifle

| Approach | Result | Faces |
|----------|--------|-------|
| Mirror modifier + apply | Right half only (silent failure) | 102 |
| Direct bmesh + manual symmetry | Full weapon | 3744 |

Switching from modifier to direct mesh was the single fix that produced a usable model.
