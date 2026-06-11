#!/usr/bin/env python3
"""STL 2D Line-Art Preview Generator
Reads a binary STL file and generates 4-view line-art previews using PIL.
No Blender required. Reliable fallback when EEVEE headless rendering fails.

Usage:
    python3 stl_2d_preview.py model.stl --output-prefix preview --views front side top iso

Dependencies: pip3 install Pillow numpy

LIMITATIONS:
- PIL polygon rendering of thin, elongated triangles (from side-extrusion models)
  can produce banding/striping artifacts. Each triangle is drawn as filled polygon
  overlapping its neighbors, creating visible seams.
- For extruded side-profile models (where triangles are long/narrow), the banding
  may make the silhouette edges look jagged. Always send the raw STL file via
  MEDIA: alongside the preview for these models.
- Very large STL files (>100K triangles) should use --sample 0.1 for faster previews.
"""

import numpy as np
import math
import argparse
import os
from PIL import Image, ImageDraw


def read_stl_vertices(filepath, sample_ratio=1.0, seed=42):
    """Read triangles from binary STL file.
    Returns list of triangles and counts.
    """
    with open(filepath, 'rb') as f:
        data = f.read()

    num_tris = int.from_bytes(data[80:84], 'little')

    # Sampling for large files
    if sample_ratio < 1.0:
        import random
        rng = random.Random(seed)
        keep = set(rng.sample(range(num_tris), max(1, int(num_tris * sample_ratio))))
    else:
        keep = None

    tris = []
    for i in range(num_tris):
        if keep is not None and i not in keep:
            continue
        offset = 84 + i * 50
        tri = []
        for j in range(3):
            v = np.frombuffer(data[offset + 12 + j*12: offset + 24 + j*12], dtype=np.float32)
            tri.append(v)
        tris.append(tri)

    return np.array(tris), len(tris), num_tris


def compute_auto_scale(triangles, target_size=800):
    """Compute scale factor so model fills ~70% of target_size."""
    all_verts = triangles.reshape(-1, 3)
    center = all_verts.mean(axis=0)
    max_range = max(all_verts.ptp(axis=0))
    if max_range < 0.001:
        max_range = 10  # fallback
    scale = (target_size * 0.7) / max_range
    return center, scale


def project_2d(tri_verts, rot_x=0, rot_y=0, rot_z=0,
               img_size=1200, center=(0, 0, 0), scale=2.0):
    """Project 3D triangle vertices to 2D with rotation.
    rot_x/rot_y/rot_z in degrees.
    Y -> screen depth, Z -> screen Y (up).
    """
    rx, ry, rz = map(math.radians, [rot_x, rot_y, rot_z])
    cx, cy = img_size / 2, img_size / 2

    def _rotate(v):
        x, y, z = v - center
        # Y-axis rotation
        x, z = x*math.cos(ry) + z*math.sin(ry), -x*math.sin(ry) + z*math.cos(ry)
        # X-axis rotation
        y, z = y*math.cos(rx) - z*math.sin(rx), y*math.sin(rx) + z*math.cos(rx)
        # Z-axis rotation (top-down)
        x, y = x*math.cos(rz) - y*math.sin(rz), x*math.sin(rz) + y*math.cos(rz)
        return (cx + x*scale, cy - z*scale)  # Z projects to screen Y

    return [_rotate(v) for v in tri_verts]


def render_view(triangles, rot_x=0, rot_y=0, rot_z=0,
                img_size=1200, fill='lightblue', outline='darkblue',
                center=None, scale=None):
    """Render a single view of the model."""
    if center is None or scale is None:
        center, scale = compute_auto_scale(triangles, img_size)

    img = Image.new('RGB', (img_size, img_size), 'white')
    draw = ImageDraw.Draw(img)

    for tri in triangles:
        pts_2d = project_2d(tri, rot_x, rot_y, rot_z,
                           img_size, center, scale)
        draw.polygon(pts_2d, fill=fill, outline=outline, width=1)

    return img


def generate_stl_preview(stl_path, output_prefix='preview',
                         img_size=1200, sample_ratio=1.0,
                         views=None):
    """Generate multi-view line-art previews from a binary STL file.

    Args:
        stl_path: Path to binary STL file
        output_prefix: Output filename prefix
        img_size: Image size in pixels (square)
        sample_ratio: Sample fraction for large files (0.1 = 10%)
        views: List of (name, rot_x, rot_y, rot_z) tuples
    """
    if views is None:
        views = [
            ('side',   0, 0, 0),   # side view
            ('front',  0, 90, 0),  # front view
            ('top',    90, 0, 0),  # top view
            ('iso',    30, 45, 0), # isometric
        ]

    triangles, total_tris, num_tris = read_stl_vertices(stl_path, sample_ratio)
    pct = sample_ratio * 100 if sample_ratio < 1.0 else 100
    center, scale = compute_auto_scale(triangles, img_size)

    outputs = []
    for name, rx, ry, rz in views:
        img = render_view(triangles, rx, ry, rz, img_size,
                         center=center, scale=scale)
        out_path = f"{output_prefix}_{name}.png"
        img.save(out_path)
        outputs.append(out_path)
        print(f"  Saved: {out_path} ({os.path.getsize(out_path)//1024}KB)")

    return outputs, total_tris, num_tris, pct


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='STL 2D Line-Art Preview Generator')
    parser.add_argument('stl_file', help='Path to binary STL file')
    parser.add_argument('--output-prefix', '-o', default='preview',
                       help='Output file prefix (default: preview)')
    parser.add_argument('--size', type=int, default=1200,
                       help='Image size in pixels (default: 1200)')
    parser.add_argument('--sample', type=float, default=1.0,
                       help='Sample ratio for large files, e.g. 0.1 (default: 1.0)')
    parser.add_argument('--views', nargs='+', default=['front', 'side', 'top', 'iso'],
                       help='Views to render: front side top iso (default: all 4)')

    args = parser.parse_args()

    if not os.path.exists(args.stl_file):
        print(f"Error: File not found: {args.stl_file}")
        exit(1)

    view_defs = {
        'side':  (0, 0, 0),
        'front': (0, 90, 0),
        'top':   (90, 0, 0),
        'iso':   (30, 45, 0),
    }

    views = [(v, *view_defs[v]) for v in args.views if v in view_defs]
    if not views:
        print("Available views: front, side, top, iso")
        exit(1)

    outputs, rendered, total, pct = generate_stl_preview(
        args.stl_file, args.output_prefix, args.size, args.sample, views
    )

    print(f"\n=== Summary ===")
    print(f"  STL: {args.stl_file} ({total} triangles total)")
    print(f"  Rendered: {rendered}/{total} ({pct:.0f}%)")
    print(f"  Views: {', '.join(args.views)}")
    print(f"  Outputs: {', '.join(outputs)}")
