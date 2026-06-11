# Contour Extraction + Smoothing Pipeline for Side-Profile Extrusion

A proven workflow for extracting smooth side-profile contours from reference images and using them for Blender bmesh side-profile extrusion modeling.

## Overview

```
Reference Image (side view) → Vision AI analysis → Contour point extraction
→ Gaussian smoothing → Downsampling → Blender bmesh side-extrude → STL
```

## Step 1: Extract Contour Points from Reference Image

Use a Python script to read an image and extract the object's silhouette outline:

```python
import numpy as np
from PIL import Image

def extract_contour_points(image_path, num_samples=400):
    """
    Extract contour points from a side-view reference image.
    Assumes dark object on light/transparent background.
    Returns left_contour, right_contour lists of (x, y) points.
    """
    img = Image.open(image_path)
    arr = np.array(img)
    
    # If RGBA, use alpha channel
    if arr.shape[2] == 4:
        mask = arr[:, :, 3] > 128
    else:
        # Convert to grayscale and threshold
        gray = np.mean(arr[:, :, :3], axis=2)
        # Otsu-like: assume object is dark, bg is light
        mask = gray < 128
    
    height, width = mask.shape
    
    left_contour = []
    right_contour = []
    
    for y in range(height):
        row = mask[y, :]
        obj_pixels = np.where(row)[0]
        if len(obj_pixels) > 0:
            left_contour.append((obj_pixels[0], y))
            right_contour.append((obj_pixels[-1], y))
    
    # Sample to desired number of points
    if len(left_contour) > num_samples:
        indices = np.linspace(0, len(left_contour)-1, num_samples, dtype=int)
        left_contour = [left_contour[i] for i in indices]
        right_contour = [right_contour[i] for i in indices]
    
    return left_contour, right_contour
```

## Step 2: Gaussian Smoothing (No scipy)

When scipy is not available (GFW download issues), use numpy convolution:

```python
def gaussian_kernel_1d(sigma=3.0, size=None):
    """Generate 1D Gaussian kernel"""
    if size is None:
        size = int(6 * sigma) | 1  # Make odd
    x = np.arange(-(size//2), size//2 + 1)
    kernel = np.exp(-x**2 / (2 * sigma**2))
    return kernel / kernel.sum()

def smooth_contour(points, sigma=3.0):
    """
    Smooth a list of (x, y) points with Gaussian convolution.
    sigma=3.0: moderate smoothing (removes jagged edges, keeps major features)
    sigma=5.0: heavy smoothing (rounds off details)
    """
    pts = np.array(points)
    kernel = gaussian_kernel_1d(sigma)
    
    # Pad to handle edges
    pad = len(kernel) // 2
    padded_x = np.pad(pts[:, 0], pad, mode='edge')
    padded_y = np.pad(pts[:, 1], pad, mode='edge')
    
    smoothed_x = np.convolve(padded_x, kernel, mode='valid')
    smoothed_y = np.convolve(padded_y, kernel, mode='valid')
    
    return list(zip(smoothed_x, smoothed_y))

def sample_contour(points, num_samples=160):
    """Evenly sample a contour to N points"""
    pts = np.array(points)
    n = len(pts)
    indices = np.linspace(0, n-1, num_samples, dtype=int)
    return pts[indices]
```

## Step 3: Visualization (Quality Check)

Always verify the smoothed contour quality before using in Blender:

```python
from PIL import Image, ImageDraw, ImageFont

def debug_contour(original_points, smoothed_points, image_path, output_path):
    """Overlay smoothed contour on original reference image"""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Draw original (noisy) contour in blue
    for x, y in original_points[::10]:  # sample every 10th
        draw.ellipse([x-1, y-1, x+1, y+1], fill='blue')
    
    # Draw smoothed contour in red
    for x, y in smoothed_points:
        draw.ellipse([x-2, y-2, x+2, y+2], fill='red')
    
    img.save(output_path)
```

**Quality criteria:**
- Smooth contour should follow the original shape within ~3-5px
- No sharp zig-zags (sigma too low)
- No loss of major features like muzzle, grip, stock (sigma too high)
- For weapons: sigma=3.0 typically works best; for organic shapes: sigma=2.0

## Step 4: Blender bmesh Side-Extrusion

```python
import bpy
import bmesh
import numpy as np

def build_side_extrusion(left_points, right_points, thickness=10.0):
    """
    Build a 3D mesh by extruding a side profile.
    
    left_points, right_points: arrays of (x, y) — the object silhouette
    thickness: how thick to extrude (Z-axis for side-profile extrusion)
    
    Convention:
      - X = width (horizontal in image)
      - Y = depth (extrusion direction)
      - Z = height (vertical in image)
    """
    mesh = bpy.data.meshes.new("SideProfile")
    bm = bmesh.new()
    
    # Add vertices along top edge (right points, reversed for winding)
    # then bottom edge (left points)
    
    # Rotate image coordinates: image X→3D X, image Y→3D Z
    N = len(left_points)
    top_verts = []
    bot_verts = []
    
    for x, y in left_points:
        top_verts.append(bm.verts.new((x, -thickness/2, y)))
        bot_verts.append(bm.verts.new((x, thickness/2, y)))
    
    # Add faces between top and bottom contours
    n = len(top_verts)
    for i in range(n - 1):
        bm.faces.new([
            top_verts[i], top_verts[i+1],
            bot_verts[i+1], bot_verts[i]
        ])
    
    # Close ends
    bm.faces.new([top_verts[0], bot_verts[0], bot_verts[-1], top_verts[-1]])
    
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new("SideExtrude", mesh)
    bpy.context.collection.objects.link(obj)
    return obj
```

## Important: Point Count Trade-offs

| Points | Faces | Quality | Use case |
|--------|-------|---------|----------|
| 50-80 | 200-320 | Rough | Quick shape check |
| 120-200 | 480-800 | Medium | Standard weapon models |
| 300-500 | 1200-2000 | High | Fine detail needed |
| 1000+ | 4000+ | Very high | Production quality |

**Key lesson:** 50 points produces a 476-face model (v5 in this session) that has visible faceting. 160+ points after smoothing produces a smooth silhouette.

## When to Use This vs. Other Approaches

| Approach | Best For | Why |
|----------|---------|-----|
| **Contour extrusion** (this doc) | Flat/2D-profile objects: weapons, sword blades, shields, tools, silhouettes | Fast, follows reference closely, fewest iterations |
| **Box composition** | Blocky/geometric objects: buildings, crates, simple mecha | Pure numpy-stl, no Blender |
| **Sphere/cylinder + boolean UNION** | Organic/round objects: characters, animals, vehicles | Smooth curves, subdiv surfaces |
| **Bambu AI + edit-mode fix** | Complex existing STL (50K+ faces) where you make minor edits | Preserves existing detail |
