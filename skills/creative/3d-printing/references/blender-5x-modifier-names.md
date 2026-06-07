# Blender 5.x Modifier & Operator API Notes

Verified on Blender 5.1.2 (hash ec6e62d40fa9, built 2026-05-19).

## Modifier Names (English — NOT localized)

In Blender 5.x, modifier names are always **English**, regardless of system language:

| Intended Modifier | Name in Script |
|-------------------|----------------|
| Boolean | `'Boolean'` |
| Bevel | `'Bevel'` |
| Subdivision Surface | `'Subdivision'` (type=`SUBSURF`) |
| Array | `'Array'` |
| Mirror | `'Mirror'` |
| Solidify | `'Solidify'` |

**DO NOT** use localized names like `'布尔'`, `'倒角'` — they cause `KeyError`.

```python
# Correct
bpy.ops.object.modifier_add(type='BOOLEAN')
mod = obj.modifiers['Boolean']  # NOT '布尔'

bpy.ops.object.modifier_add(type='BEVEL')
mod = obj.modifiers['Bevel']    # NOT '倒角'
```

## STL Export Parameters (Blender 5.0+)

Previous Blender 4.x:
```python
bpy.ops.wm.stl_export(use_selection=True, ascii=False)
```

Blender 5.x:
```python
bpy.ops.wm.stl_export(
    filepath=path,
    export_selected_objects=True,    # NOT use_selection
    ascii_format=False,              # NOT ascii
    global_scale=10.0,               # mm scale
)
```

Missing/wrong keyword arguments cause `TypeError: Converting py args to operator properties:: keyword "X" unrecognized`.

## Render Engine Enum

```python
scene.render.engine = 'BLENDER_EEVEE'   # NOT 'EEVEE'
```

## EEVEE Properties Removed in 5.x

The following properties no longer exist on `scene.eevee`:
- `use_bloom` — removed
- `use_ssr` — removed
- `use_motion_blur` — removed

Just skip them; defaults are fine.

## Render Environment Change in 5.x

`film_transparent` behavior changed subtly in 5.x. With `film_transparent=True` and a default dark world background, small or dark-colored models can appear **completely invisible** in the output — the transparent film + dark world produce an all-black image.

**Fix:** Always set `film_transparent=False` and explicitly set a light-colored world background:
```python
scene.render.film_transparent = False
world = scene.world
if not world.use_nodes:
    world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value = (0.92, 0.92, 0.92, 1.0)
    bg.inputs['Strength'].default_value = 1.0
```

## Light Setup Required in Headless Mode

Blender headless starts with only a default point light which is often insufficient for visibility. Always add at least 3 lights explicitly in your render script:

```python
# Main light (warm, front-right-top)
bpy.ops.object.light_add(type='AREA', location=(10, -8, 12))
main = bpy.context.object
main.data.energy = 500
main.data.color = (1.0, 0.9, 0.7)

# Fill light (cool, back-left)
bpy.ops.object.light_add(type='AREA', location=(-8, 8, 5))
fill = bpy.context.object
fill.data.energy = 300
fill.data.color = (0.7, 0.8, 1.0)

# Rim light (sun, from behind)
bpy.ops.object.light_add(type='SUN', location=(0, 10, 5))
rim = bpy.context.object
rim.data.energy = 2.0
```

## Material API Deprecation

```python
mat.use_nodes = True  # DeprecationWarning in 5.x, removed in 6.0
```

For now it still works (warning only). In 6.0 this will need a different approach.

## BMesh `ensure_lookup_table()`

After adding vertices with `bm.verts.new()`, always call `bm.verts.ensure_lookup_table()` before accessing `bm.verts[-1]` or iterating. Otherwise you get:

```
BMElemSeq[index]: outdated internal index table, run ensure_lookup_table() first
```

This applies to `bm.edges` and `bm.faces` too — call each after modifications before reading by index.
