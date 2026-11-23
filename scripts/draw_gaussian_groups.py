#!/usr/bin/env python3
"""Show one actual cabinet Gaussian, twelve neighbours, and the complete set.

All panels use samples from the shared cabinet, not an image blur. Ellipsoid
guides are two-standard-deviation contours, not Gaussian support boundaries.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from animate_gaussian_cabinet import CENTERS, COVS, COLORS, NAMES, SELECTED, _SAMPLES, blend_splats
from draw_representation_overview import EYE, RIGHT, UP
from preview_shared_cabinet import font

OUT = Path(__file__).resolve().parents[1] / 'book/assets/diagrams'
W, H = 600, 560
INK, MUTED, BLUE, GOLD = '#293632', '#626c68', '#376b91', '#a67a20'
BASIS = np.array([RIGHT, -UP])
candidate = np.flatnonzero((NAMES == NAMES[SELECTED]) & (_SAMPLES.normals[:, 1] < -.9))
GROUP = candidate[np.argsort(np.linalg.norm(CENTERS[candidate] - CENTERS[SELECTED], axis=1))[:12]]
assert GROUP[0] == SELECTED and len(set(GROUP)) == 12


def project(points, center, scale, anchor=(300, 300)):
    return (np.asarray(points) - center) @ BASIS.T * scale + anchor


def splats(indices, center, scale, opacity):
    matrix = BASIS * scale
    return blend_splats(project(CENTERS[indices], center, scale),
                        matrix @ COVS[indices] @ matrix.T, COLORS[indices],
                        -CENTERS[indices] @ EYE, W, H, opacity).convert('RGB')


def guide(draw, index, center, scale, selected=False, width=2):
    values, vectors = np.linalg.eigh(COVS[index])
    axes = vectors @ np.diag(2 * np.sqrt(values))
    angles = np.linspace(0, 2 * np.pi, 160)
    for a, b in ((0, 1), (0, 2), (1, 2)):
        ring = CENTERS[index] + np.cos(angles)[:, None] * axes[:, a] + np.sin(angles)[:, None] * axes[:, b]
        draw.line([tuple(p) for p in project(ring, center, scale)], fill=GOLD if selected else '#7a9db5', width=width)


def label(draw, xy, text, size=27, color=INK, bold=False):
    draw.text(xy, text, font=font(size, bold), fill=color, anchor='mm')


def heading(draw, title, subtitle):
    draw.rectangle((0, 0, W, 99), fill='white')
    label(draw, (300, 40), title, 32, bold=True)
    label(draw, (300, 78), subtitle, 23, MUTED)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    center = CENTERS[SELECTED]
    im = splats(np.array([SELECTED]), center, 1650, .64)
    draw = ImageDraw.Draw(im)
    guide(draw, SELECTED, center, 1650, width=3)
    draw.ellipse((291, 291, 309, 309), fill=GOLD, outline='white', width=2)
    heading(draw, '1 Gaussian', 'One small region, enlarged')
    label(draw, (300, 514), 'Gold dot = the selected center', 23, GOLD)
    im.save(OUT / 'gaussian-one-blob.png')

    center = CENTERS[GROUP].mean(axis=0)
    im = splats(GROUP, center, 900, .24)
    draw = ImageDraw.Draw(im)
    for index in GROUP[::-1]:
        guide(draw, index, center, 900, selected=index == SELECTED)
    for number, index in enumerate(GROUP, 1):
        x, y = project(CENTERS[index], center, 900)
        selected = index == SELECTED
        draw.ellipse((x-14, y-14, x+14, y+14), fill=GOLD if selected else 'white', outline=GOLD if selected else BLUE, width=2)
        label(draw, (x, y), str(number), 18, 'white' if selected else BLUE)
    heading(draw, '12 nearby Gaussians', 'A small patch on the blue drawer')
    label(draw, (300, 514), 'Each numbered dot is one center', 23, MUTED)
    im.save(OUT / 'gaussian-local-group.png')

    center = np.array([0., 0., 0.])
    scale = 181
    im = splats(np.arange(len(CENTERS)), center, scale, .94)
    draw = ImageDraw.Draw(im)
    # The outline encloses the same group's 2-sigma guides in this view.
    radius = 2 * np.sqrt(np.diagonal(COVS[GROUP], axis1=1, axis2=2)).max(axis=0)
    lo, hi = CENTERS[GROUP].min(axis=0)-radius, CENTERS[GROUP].max(axis=0)+radius
    y = CENTERS[SELECTED, 1]-.02
    corners = np.array([[lo[0],y,lo[2]],[hi[0],y,lo[2]],[hi[0],y,hi[2]],[lo[0],y,hi[2]]])
    xy = project(corners, center, scale)
    draw.line([tuple(p) for p in np.vstack([xy,xy[0]])], fill='white', width=6)
    draw.line([tuple(p) for p in np.vstack([xy,xy[0]])], fill=GOLD, width=3)
    x,y = project(CENTERS[SELECTED], center, scale)
    draw.ellipse((x-4,y-4,x+4,y+4),fill=GOLD,outline='white',width=1)
    heading(draw, f'{len(CENTERS):,} Gaussians', 'Their projected colors blend together')
    label(draw, (300, 526), 'Gold outline = the same small patch', 23, GOLD)
    im.save(OUT / 'gaussian-whole-cabinet.png')
    (OUT/'gaussian-groups.json').write_text(json.dumps({
        'source':'shared_cabinet.gaussians(spacing=.085)',
        'total_count':len(CENTERS), 'selected_index':int(SELECTED),
        'selected_center_m':CENTERS[SELECTED].tolist(),
        'local_indices':GROUP.tolist(), 'guide_extent_standard_deviations':2,
        'note':'Scripted teaching samples; not a trained 3DGS reconstruction.'
    },indent=2)+'\n')
    print(f'Rendered one selected Gaussian, its {len(GROUP)}-sample neighbourhood, and all {len(CENTERS)} samples.')


if __name__ == '__main__':
    main()
