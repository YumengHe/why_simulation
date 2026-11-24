#!/usr/bin/env python3
"""Known cabinet correspondences illustrate image matching, not COLMAP output."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from draw_dust3r_examples import raster, camera, label, PAPER, CORAL, BLUE, GOLD, MUTED, FOCAL, W, H

OUT = Path(__file__).resolve().parents[1] / 'book/assets/colmap'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    views = [raster(-28), raster(0)]
    points = views[0][1]
    targets = [np.array([-.48, -.49, .70]), np.array([-.21, -.68, .53]), np.array([.48, -.49, -.70])]
    chosen = []
    for target in targets:
        v, u = np.unravel_index(np.nanargmin(np.linalg.norm(points-target, axis=2)), points.shape[:2])
        chosen.append(points[v, u])
    im = Image.new('RGB', (1200, 790), PAPER)
    d = ImageDraw.Draw(im)
    label(d, (600, 42), 'Match the same details across photographs', 40, bold=True)
    label(d, (600, 94), 'Each line connects two views of one physical point.', 29, MUTED)
    projected = []
    for i, (angle, name) in enumerate([(-28, 'Left photograph'), (0, 'Front photograph')]):
        x, y = 40+i*600, 158
        im.paste(views[i][0].resize((520, 520), Image.Resampling.LANCZOS), (x, y))
        d = ImageDraw.Draw(im)
        label(d, (x+260, 142), name, 28, bold=True)
        d.rectangle((x, y, x+520, y+520), outline='#dedfd7', width=2)
        origin, basis = camera(angle)
        loc = (np.array(chosen)-origin)@basis.T
        uv = FOCAL*loc[:, :2]/loc[:, 2, None]+[W/2, H/2]
        for p, coord in zip(chosen, uv):
            hit = views[i][1][int(coord[1]), int(coord[0])]
            assert np.isfinite(hit).all() and np.linalg.norm(hit-p)<.012
        projected.append(uv*(520/600)+[x, y])
    overlay = Image.new('RGBA', im.size)
    od = ImageDraw.Draw(overlay)
    for a, b, color in zip(*projected, [CORAL, BLUE, GOLD]):
        od.line([tuple(a), tuple(b)], fill=color+'a0', width=3)
    im = Image.alpha_composite(im.convert('RGBA'), overlay).convert('RGB')
    d = ImageDraw.Draw(im)
    for coords in projected:
        for p, name, color in zip(coords, 'ABC', [CORAL, BLUE, GOLD]):
            x, y = p
            d.ellipse((x-8, y-8, x+8, y+8), fill=color, outline='white', width=3)
            d.rounded_rectangle((x-37, y-41, x-3, y-3), radius=7, fill=PAPER, outline=color, width=2)
            label(d, (x-20, y-22), name, 31, color, True)
    label(d, (600, 725), 'A: drawer corner     B: handle detail     C: door corner', 29, MUTED)
    label(d, (600, 765), 'Illustrative matches; real photographs supply many more.', 27, MUTED)
    im.save(OUT/'matched-details.png')
    (OUT/'manifest.json').write_text(json.dumps({
        'generator':'scripts/draw_colmap_matches.py',
        'geometry':'scripts/shared_cabinet.py',
        'provenance':'Known geometric correspondences rendered by script; not detected COLMAP features or reconstruction results.',
        'matched_points_world':[p.tolist() for p in chosen],
        'checks':'Every labeled world point is visible in both views at its projected pixel.',
        'source':'https://colmap.github.io/tutorial.html#feature-matching-and-geometric-verification',
    }, indent=2)+'\n')
    print('Created COLMAP correspondence illustration; checked all three points in both views.')


if __name__ == '__main__':
    main()
