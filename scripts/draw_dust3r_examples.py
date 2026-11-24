#!/usr/bin/env python3
"""Pixel/pointmap/cloud and alignment lessons from the shared cabinet.

No learned model is run. Perspective rasterization supplies a surface position
for each visible pixel. The point cloud uses those very positions. Alignment
uses a prescribed coordinate mismatch and a fitted similarity transform on
known shared points, illustrating the role of alignment, not DUSt3R's optimizer.
"""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw
from shared_cabinet import mesh, validate
from preview_shared_cabinet import font

OUT = Path(__file__).resolve().parents[1] / 'book/assets/dust3r'
PAPER = (254, 253, 251)
INK, MUTED, LINE = '#293632', '#5f6862', '#d9ddd8'
BLUE, GOLD, CORAL = '#447ca4', '#aa7c25', '#bd5845'
W = H = 600
FOCAL = 760.
TARGET_A = np.array([-.48, -.49, .70])


def camera(angle):
    a = math.radians(angle)
    origin = np.array([3.4*math.sin(a), -3.4*math.cos(a), 1.35])
    forward = np.array([0., -.1, 0.]) - origin
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0., 0., 1.]); right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    return origin, np.array([right, down, forward])


def raster(angle):
    """Return an opaque render, world pointmap and per-pixel surface colors."""
    model = mesh(n=32)
    origin, basis = camera(angle)
    pixels = np.full((H, W, 3), PAPER, dtype=float)
    colors = pixels.copy()
    points = np.full((H, W, 3), np.nan)
    nearest = np.full((H, W), -np.inf)
    light = np.array([-3., -5., 7.]); light /= np.linalg.norm(light)
    for tri, color in zip(model.triangles, model.colors):
        normal = np.cross(tri[1]-tri[0], tri[2]-tri[0]); normal /= np.linalg.norm(normal)
        if normal @ (origin-tri.mean(axis=0)) <= 0: continue
        local = (tri-origin) @ basis.T
        depth = local[:, 2]
        assert np.all(depth > 0)
        uv = FOCAL*local[:, :2]/depth[:, None] + [W/2, H/2]
        x0, y0 = np.maximum(np.floor(uv.min(axis=0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(uv.max(axis=0)).astype(int)+1, [W, H])
        if x1 <= x0 or y1 <= y0: continue
        yy, xx = np.mgrid[y0:y1, x0:x1]; xx = xx+.5; yy = yy+.5
        a, b, c = uv
        den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den) < 1e-10: continue
        wa = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        wb = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
        wc = 1-wa-wb
        invz = wa/depth[0]+wb/depth[1]+wc/depth[2]
        old = nearest[y0:y1, x0:x1]
        visible = (wa>=-1e-9)&(wb>=-1e-9)&(wc>=-1e-9)&(invz>old)
        numerator = (wa[..., None]*tri[0]/depth[0] +
                     wb[..., None]*tri[1]/depth[1] + wc[..., None]*tri[2]/depth[2])
        world = numerator / np.where(abs(invz)>1e-12, invz, 1)[..., None]
        points[y0:y1, x0:x1][visible] = world[visible]
        colors[y0:y1, x0:x1][visible] = color
        pixels[y0:y1, x0:x1][visible] = color*(.65+.35*max(0, normal@light))
        old[visible] = invz[visible]
    return Image.fromarray(np.uint8(pixels)), points, colors


def label(draw, xy, value, size=30, color=INK, bold=False, anchor='mm'):
    draw.text(xy, value, font=font(size, bold), fill=color, anchor=anchor)


def mark(draw, xy, text='A', color=CORAL, offset=(-35, -38)):
    x, y = xy
    draw.ellipse((x-7, y-7, x+7, y+7), fill=color, outline='white', width=2)
    end = (x+offset[0], y+offset[1])
    draw.line((x, y, *end), fill=color, width=2)
    label(draw, end, text, 32, color, True)


def selected_pixel(points):
    distances = np.linalg.norm(points-TARGET_A, axis=2)
    v, u = np.unravel_index(np.nanargmin(distances), distances.shape)
    assert np.isfinite(points[v-2:v+3, u-2:u+3]).all()
    return int(u), int(v)


def pointmap_diagram(u, v, coordinate):
    im = Image.new('RGB', (600, 680), PAPER); d = ImageDraw.Draw(im)
    label(d, (300, 38), 'Pointmap: keep the pixel grid', 30, bold=True)
    label(d, (300, 82), 'A small patch around pixel A', 25, MUTED)
    cell, left, top = 72, 120, 155
    label(d, (300, 125), 'Image columns', 25, MUTED)
    for row in range(5):
        for col in range(5):
            x, y = left+col*cell, top+row*cell
            selected = (row, col)==(2, 2)
            d.rectangle((x, y, x+cell, y+cell), fill='#f8e9e4' if selected else 'white',
                        outline=CORAL if selected else LINE, width=3 if selected else 1)
            label(d, (x+cell/2, y+cell/2), 'A' if selected else 'XYZ', 23,
                  CORAL if selected else MUTED, selected)
    label(d, (300, 547), f'Pixel A: column {u}, row {v}', 27, bold=True)
    label(d, (300, 590), '('+', '.join(f'{x:.2f}' for x in coordinate)+')', 31, CORAL, True)
    label(d, (300, 638), 'Each cell stores a 3D position.', 26, MUTED)
    return im


def sampled(points, colors, step=7):
    p, c = points[::step, ::step], colors[::step, ::step]
    valid = np.isfinite(p).all(axis=2)
    return p[valid], c[valid]


def plot(points, colors, title, subtitle, marker_points=(), scale=235., center=(0., -.1, 0.)):
    im = Image.new('RGB', (600, 680), PAPER); d = ImageDraw.Draw(im)
    eye = np.array([2.8, -6., 2.5]); eye /= np.linalg.norm(eye)
    right = np.cross([0., 0., 1.], eye); right /= np.linalg.norm(right)
    up = np.cross(eye, right)
    def project(p):
        q = np.asarray(p)-center
        return np.stack([300+scale*(q@right), 370-scale*(q@up)], axis=-1)
    # A ground grid makes the spatial view distinct from the image-index grid.
    for t in np.linspace(-1.2, 1.2, 7):
        for line in ([[t, -1.2, -.89], [t, 1.2, -.89]],
                     [[-1.2, t, -.89], [1.2, t, -.89]]):
            d.line([tuple(q) for q in project(line)], fill='#e9ece7', width=1)
    xy = project(points)
    for i in np.argsort(points@eye):
        x, y = xy[i]
        col = colors if isinstance(colors, str) else tuple(np.uint8(colors[i]))
        d.ellipse((x-1.7, y-1.7, x+1.7, y+1.7), fill=col)
    for p, name, color, offset in marker_points:
        mark(d, project(p), name, color, offset)
    label(d, (300, 35), title, 31, bold=True)
    label(d, (300, 78), subtitle, 25, MUTED)
    return im


def similarity(source, target):
    """Least-squares scale/rotation/translation for known corresponding points."""
    a, b = source.mean(0), target.mean(0)
    x, y = source-a, target-b
    u, singular, vt = np.linalg.svd(x.T@y)
    correction = np.eye(3); correction[-1, -1] = np.linalg.det(u@vt)
    rotation = u@correction@vt
    scale = np.sum(singular*np.diag(correction))/np.sum(x*x)
    translation = b-scale*a@rotation
    return scale, rotation, translation


def main():
    OUT.mkdir(parents=True, exist_ok=True); validate(32)
    views = {}
    for name, angle in [('left', -28), ('front', 0), ('right', 28)]:
        im, pts, cols = raster(angle); views[name] = (im, pts, cols)
        framed = Image.new('RGB', (600, 680), PAPER); framed.paste(im, (0, 70))
        label(ImageDraw.Draw(framed), (300, 38), name.capitalize()+' view', 32, bold=True)
        framed.save(OUT/f'view-{name}.png')
    im, points, colors = views['left']
    u, v = selected_pixel(points); a_world = points[v, u]
    origin, basis = camera(-28)
    a_local = (a_world-origin)@basis.T
    # A pointmap's XYZ value projects back to exactly the associated pixel.
    assert np.allclose(FOCAL*a_local[:2]/a_local[2]+[W/2, H/2], [u+.5, v+.5])
    frame = Image.new('RGB', (600, 680), PAPER); frame.paste(im, (0, 70))
    d = ImageDraw.Draw(frame)
    label(d, (300, 35), 'Image: choose a pixel', 31, bold=True)
    mark(d, (u+.5, v+70.5))
    label(d, (300, 645), f'A: column {u}, row {v}', 27, MUTED)
    frame.save(OUT/'image-pixel.png')
    pointmap_diagram(u, v, a_local).save(OUT/'pointmap-grid.png')
    cloud, cloud_colors = sampled(points, colors, 6)
    # Preserve A even if the decimation grid does not pass through its pixel.
    cloud = np.vstack([cloud, a_world]); cloud_colors = np.vstack([cloud_colors, colors[v, u]])
    cloud_im = plot(cloud, cloud_colors, 'Point cloud: place the XYZ points',
                    'Same coordinates, viewed in 3D', [(a_world, 'A', CORAL, (-38, -40))])
    label(ImageDraw.Draw(cloud_im), (300, 645), 'Colors come from the input image.', 25, MUTED)
    cloud_im.save(OUT/'point-cloud.png')
    pc = {name: sampled(p, c, 8)[0] for name, (_, p, c) in views.items()}
    pair1 = np.vstack([pc['left'], pc['front']])
    pair2 = np.vstack([pc['front'], pc['right']])
    # Both pointmaps within each pair already share a frame. Introduce a
    # mismatch BETWEEN pair results to demonstrate what joint alignment solves.
    theta = math.radians(16)
    rotation = np.array([[math.cos(theta), -math.sin(theta), 0.],
                         [math.sin(theta), math.cos(theta), 0.], [0., 0., 1.]])
    shift = np.array([.48, .16, .10]); stretch = .88
    mismatch = lambda p: stretch*np.asarray(p)@rotation.T+shift
    scale, rot, trans = similarity(mismatch(pc['front']), pc['front'])
    aligned = scale*mismatch(pair2)@rot+trans
    error = float(np.sqrt(np.mean((aligned-pair2)**2)))
    assert error < 1e-10
    b = a_world  # Keep the same labeled surface point throughout the lesson.
    for before in (True, False):
        p2 = mismatch(pair2) if before else aligned
        pts = np.vstack([pair1, p2])
        cs = np.vstack([np.tile([68, 124, 164], (len(pair1), 1)),
                        np.tile([170, 124, 37], (len(p2), 1))])
        marks = [(b, 'A', BLUE, (-38, -37))]
        if before: marks.append((mismatch(b), 'A', GOLD, (35, -40)))
        drawing = plot(pts, cs, 'Before alignment' if before else 'After alignment',
                       'Pair results use different frames' if before else 'Both pairs share one frame',
                       marks, scale=205, center=(.18, -.05, 0.))
        d = ImageDraw.Draw(drawing)
        label(d, (300, 608), 'Blue: Left + Front', 26, BLUE, True)
        label(d, (300, 648), 'Gold: Front + Right', 26, GOLD, True)
        drawing.save(OUT/('alignment-before.png' if before else 'alignment-after.png'))
    (OUT/'manifest.json').write_text(json.dumps({
        'generator': 'scripts/draw_dust3r_examples.py',
        'geometry': 'scripts/shared_cabinet.py',
        'provenance': 'Scripted teaching illustrations, not DUSt3R inference or recorded optimization.',
        'rasterization': 'Perspective-correct triangle interpolation with a depth buffer; position per visible pixel.',
        'pixel_A': {'column': u, 'row': v, 'world': a_world.tolist(), 'camera_frame': a_local.tolist()},
        'coordinate_units': 'Authored teaching units. Model predictions require a scale reference for metric measurements.',
        'pointmap_and_cloud': 'The cloud is sampled from the same position array; no new geometry is inferred during reorganization.',
        'pair_alignment': 'Known overlap between Left+Front and Front+Right. Prescribed mismatch is removed by a fitted similarity transform.',
        'alignment_rms': error,
        'scope': 'Visible surface samples only; hidden cabinet surfaces are not filled in.',
        'sources': ['https://arxiv.org/abs/2312.14132', 'https://github.com/naver/dust3r']
    }, indent=2)+'\n')
    print(f'Created 8 DUSt3R teaching figures. Pixel reprojection verified; alignment RMS {error:.2e}.')


if __name__ == '__main__': main()
