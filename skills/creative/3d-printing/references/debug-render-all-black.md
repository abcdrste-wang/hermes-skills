# Debugging "All Black" / "Uniform Gray" Renders

## Why renders fail (Mac Mini M4, no dedicated GPU)

Blender EEVEE headless rendering on this Mac Mini M4 uses software rasterization fallback. This produces two failure modes:

### Failure Mode A: All Black (pixel mean < 30)
**Root causes:**
- Camera pointing away from model (TRACK_TO constraint failed in headless mode)
- Camera too far (model is a speck in the frame)
- Camera too close (model clips out of view)
- STL model has wrong Z position (centroid at Z < 0, camera looks at origin)
- STL model is too small (e.g., 8mm wide → camera at 0.15m distance, Blender's default near clip clips it)

**Fix:** Set camera Euler angles directly (no TRACK_TO), verify STL vertex bounds first.

### Failure Mode B: Uniform Gray (pixel mean 30-80, std dev ~25-30)
**Root causes:**
- **No dedicated GPU** — EEVEE falls back to software rasterizer that produces flat-shaded, undifferentiated renders
- Lights, materials, background are all correct — the render just has no contrast
- This is NOT a configurable problem — it's a hardware limitation

**Fix:** **Skip Blender rendering entirely. Use `scripts/stl_2d_preview.py` (2D line-art, PIL + numpy).**

### Failure Mode C: Uniform Dark (all pixels < 30, std dev 0-3)

**NEW — discovered 2026-06-08 during FFAR1 v3 rendering**

While trying to get better contrast, introduced a **large white ground plane** (500×500, at Z=-0.01) plus 3 Area lights (1500/500/300 energy). The intent was: white plane + strong light → bright background → dark gray material stands out.

**Actual result:** 100% dark rendering. Every single pixel was dark (RBG mean ~16), 0% background pixels detected. The white plane was not lit by the Area lights at all — EEVEE software fallback doesn't illuminate large geometry far from the camera.

**Root cause:** Area lights on M4 software fallback have limited reach. A 500×500 plane at Z=-0.01 with the camera at Z=20-35mm is too far from the Area lights (which were placed near the camera position). The white plane never turned white in the render.

**Fix:** 
- Do NOT add large white ground planes — they don't light up in headless EEVEE
- Do NOT increase light energy to compensate (1500 vs 300 made zero difference)
- Just use the world background only (set via Background shader node, not via a geometry plane)
- If world background alone doesn't give enough contrast, switch to `stl_2d_preview.py` immediately
- Accept that headless EEVEE on M4 cannot do multi-object scene lighting

### Script to diagnose render quality before sending to user

```python
from PIL import Image; import numpy as np

def diagnose_render(path):
    img = Image.open(path).convert('RGB')
    arr = np.array(img)
    
    # 1. Basic stats
    mean, std, mn, mx = arr.mean(), arr.std(), arr.min(), arr.max()
    
    # 2. Dynamic range
    dr = mx - mn
    
    # 3. Region analysis (center vs corners)
    h, w = arr.shape[:2]
    center = arr[h//4:3*h//4, w//4:3*w//4]
    tl = arr[:h//4, :w//4]
    
    print(f"Global: mean={mean:.0f}, std={std:.1f}, range=[{mn},{mx}], DR={dr}")
    print(f"Center: mean={center.mean():.0f} | Top-left: mean={tl.mean():.0f}")
    
    if dr < 30:
        print("FAIL: Dynamic range too low — render is monochrome/flat")
    elif mean < 30:
        print("FAIL: Too dark — camera/STL issue or unlit scene")
    else:
        print("OK: Render passes")

diagnose_render('output.png')
```

### Detection Script
Run this immediately after rendering to classify the failure:
```python
from PIL import Image; import numpy as np
img = Image.open('render.png').convert('L')
arr = np.array(img)
mean, std = arr.mean(), arr.std()
if std < 5 and mean > 20:
    print(f"FAILURE TYPE B (gray): mean={mean:.0f}, std={std:.1f} — GPU-free render. Use 2D line-art.")
elif mean < 30:
    print(f"FAILURE TYPE A (black): mean={mean:.0f} — camera/STL issue. Fix settings.")
else:
    print(f"OK: mean={mean:.0f}, std={std:.1f}")
```

## Protocol for this Mac Mini M4

1. Use `scripts/stl_2d_preview.py` as PRIMARY preview method — always
2. Only attempt Blender EEVEE renders if user explicitly asks
3. If user asks for EEVEE renders, warm them: "这台 Mac Mini 没有独立显卡，EEVEE 头渲染可能会偏平面化"
