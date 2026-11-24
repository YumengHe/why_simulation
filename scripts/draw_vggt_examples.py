#!/usr/bin/env python3
"""Illustrate VGGT's input/output meanings with the canonical cabinet.

These are deterministic teaching diagrams, not VGGT predictions. The shared
perspective rasterizer provides visible surface points. Depth is camera-axis Z;
the colored cloud uses these same surface samples from all three views.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from draw_dust3r_examples import (
    raster, camera, sampled, selected_pixel, plot, label, mark,
    PAPER, INK, MUTED, BLUE, GOLD, CORAL, FOCAL, W, H,
)

OUT = Path(__file__).resolve().parents[1] / 'book/assets/vggt'
VIEWS = [('Left', -28, BLUE), ('Front', 0, GOLD), ('Right', 28, '#528b82')]
NEAR = np.array([241, 192, 88.])
FAR = np.array([57, 104, 156.])


def camera_diagram():
    im = Image.new('RGB', (600, 680), PAPER)
    d = ImageDraw.Draw(im)
    label(d, (300, 35), 'Cameras: where each view began', 30, bold=True)
    label(d, (300, 80), 'A plan view from above', 25, MUTED)
    def project(p):
        p = np.asarray(p)
        return np.array([300+110*p[0], 210-100*p[1]])
    for x in [-2, -1, 0, 1, 2]:
        d.line([tuple(project([x, .8])), tuple(project([x, -3.6]))], fill='#e9ece7')
    for y in [0, -1, -2, -3]:
        d.line([tuple(project([-2.1, y])), tuple(project([2.1, y]))], fill='#e9ece7')
    # The cabinet footprint and the same fixed drawer handle, viewed from above.
    d.rectangle((232, 167, 368, 253), fill='#6c9996', outline='#456b68', width=2)
    d.rectangle((244, 253, 356, 259), fill='#5b8db8')
    d.line((277, 259, 277, 275), fill='#929f9e', width=6)
    d.line((323, 259, 323, 275), fill='#929f9e', width=6)
    d.line((272, 275, 328, 275), fill='#cfd8d7', width=11)
    label(d, (300, 142), 'Cabinet', 27, bold=True)
    label(d, (300, 295), 'Front', 24, MUTED)
    for index, (name, angle, color) in enumerate(VIEWS, 1):
        origin, basis = camera(angle)
        forward = basis[2, :2]; forward /= np.linalg.norm(forward)
        side = np.array([-forward[1], forward[0]])
        c = origin[:2]
        plane = c + .70*forward
        a, b = plane-.29*side, plane+.29*side
        d.line([tuple(project(a)), tuple(project(c)), tuple(project(b)), tuple(project(a))], fill=color, width=3)
        # Extend the optical direction toward the model, stopping at its front.
        end = c + 2.4*forward
        d.line([tuple(project(plane)), tuple(project(end))], fill=color, width=2)
        p = project(c)
        d.ellipse((p[0]-14, p[1]-14, p[0]+14, p[1]+14), fill=color)
        label(d, p, str(index), 20, 'white', True)
        label(d, (p[0], p[1]+35), name, 25, color, True)
    label(d, (300, 628), 'Positions and viewing directions', 25, MUTED)
    label(d, (300, 660), 'Lens settings are estimated too.', 24, MUTED)
    return im


def depth_diagram(points):
    origin, basis = camera(-28)
    valid = np.isfinite(points).all(axis=2)
    z = (points-origin) @ basis[2]
    lo, hi = float(z[valid].min()), float(z[valid].max())
    t = np.zeros((H, W)); t[valid] = (z[valid]-lo)/(hi-lo)
    rgb = np.full((H, W, 3), PAPER, dtype=np.uint8)
    rgb[valid] = NEAR*(1-t[valid, None])+FAR*t[valid, None]
    im = Image.new('RGB', (600, 680), PAPER)
    im.paste(Image.fromarray(rgb).resize((490, 490), Image.Resampling.LANCZOS), (55, 90))
    d = ImageDraw.Draw(im)
    label(d, (300, 35), 'Depth: how far into this view?', 30, bold=True)
    label(d, (300, 80), 'Same pixels as the left image', 25, MUTED)
    for x in range(360):
        amount = x/359
        color = tuple(np.uint8(NEAR*(1-amount)+FAR*amount))
        d.line((120+x, 580, 120+x, 600), fill=color)
    label(d, (120, 625), 'Nearer', 24, MUTED, anchor='lm')
    label(d, (480, 625), 'Farther', 24, MUTED, anchor='rm')
    label(d, (300, 661), 'Color shows depth, not paint.', 25, MUTED)
    return im, (lo, hi)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    views = {name: raster(angle) for name, angle, _ in VIEWS}
    _, left_points, _ = views['Left']
    u, v = selected_pixel(left_points)
    point_a = left_points[v, u]
    clouds, cloud_colors, errors = [], [], []
    for index, (name, angle, color) in enumerate(VIEWS, 1):
        image, points, colors = views[name]
        origin, basis = camera(angle)
        local = (point_a-origin)@basis.T
        uv = FOCAL*local[:2]/local[2]+[W/2, H/2]
        # Verify A is visible, so all input annotations denote the same surface.
        sample = points[int(uv[1]), int(uv[0])]
        assert np.isfinite(sample).all() and np.linalg.norm(sample-point_a) < .01
        frame = Image.new('RGB', (600, 680), PAPER); frame.paste(image, (0, 70))
        d = ImageDraw.Draw(frame)
        label(d, (300, 35), f'{index}. {name} input image', 31, color, True)
        mark(d, (uv[0], uv[1]+70), color=CORAL)
        label(d, (300, 645), 'A: the same drawer corner', 25, MUTED)
        frame.save(OUT/f'input-{name.lower()}.png')
        p, c = sampled(points, colors, 6)
        clouds.append(p); cloud_colors.append(c)
        # Camera + axis-depth must reconstruct the original per-pixel position.
        yy, xx = np.mgrid[:H, :W]
        valid = np.isfinite(points).all(axis=2)
        cam = (points-origin)@basis.T
        rays = np.stack([(xx+.5-W/2)/FOCAL, (yy+.5-H/2)/FOCAL, np.ones_like(xx)], axis=-1)
        reconstructed = (rays*cam[..., 2, None])@basis+origin
        error = float(np.max(np.linalg.norm(reconstructed[valid]-points[valid], axis=1)))
        assert error < 1e-10
        errors.append(error)
    camera_diagram().save(OUT/'camera-views.png')
    depth, depth_range = depth_diagram(left_points)
    depth.save(OUT/'depth-map.png')
    cloud = plot(np.vstack(clouds), np.vstack(cloud_colors),
                 '3D points: the visible surfaces', 'Samples from all three views',
                 [(point_a, 'A', CORAL, (-38, -40))])
    label(ImageDraw.Draw(cloud), (300, 645), 'Pointmap entries displayed together', 25, MUTED)
    cloud.save(OUT/'surface-points.png')
    (OUT/'manifest.json').write_text(json.dumps({
        'generator': 'scripts/draw_vggt_examples.py',
        'geometry': 'scripts/shared_cabinet.py',
        'rasterizer': 'scripts/draw_dust3r_examples.py',
        'provenance': 'Scripted illustrations of VGGT input and output meanings; no VGGT inference is run.',
        'views': [{'name': n, 'azimuth_degrees': a} for n, a, _ in VIEWS],
        'depth': 'Camera-axis Z, color-normalized over the visible cabinet in the left image.',
        'depth_range_authored_units': depth_range,
        'camera_depth_unprojection_max_errors': errors,
        'point_A_world': point_a.tolist(),
        'points': 'Visible surface samples from the same perspective renders, in the shared authored frame.',
        'sources': ['https://vgg-t.github.io/', 'https://github.com/facebookresearch/vggt#detailed-usage'],
    }, indent=2)+'\n')
    print(f'Created 6 VGGT teaching images; max depth-to-point error {max(errors):.2e}.')


if __name__ == '__main__':
    main()
