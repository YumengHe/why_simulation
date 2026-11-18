#!/usr/bin/env python3
"""Original schematic drawings of 3D representations, using no external assets."""
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parents[1] / 'book/assets/diagrams'
OUT.mkdir(parents=True, exist_ok=True)

# Three visible surfaces of one box, projected into the same view.
FACES = [
    ([(58, 83), (158, 42), (265, 76), (165, 117)], '#dce7e5'),
    ([(165, 117), (265, 76), (265, 176), (165, 217)], '#83aaa8'),
    ([(58, 83), (165, 117), (165, 217), (58, 183)], '#b3cdca'),
]


def point(corners, u, v):
    a, b, c, d = corners
    return tuple((1-u)*(1-v)*a[k] + u*(1-v)*b[k] + u*v*c[k] + (1-u)*v*d[k] for k in (0, 1))


def coords(points):
    return ' '.join(f'{x:.2f},{y:.2f}' for x, y in points)


def save(name, label, body):
    (OUT / f'representation-{name}.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 250" role="img">'
        f'<title>{escape(label)}</title>{body}</svg>\n')


for kind in ('points', 'triangles', 'quads', 'gaussians'):
    drawing = ''
    if kind == 'gaussians':
        drawing += '<defs><radialGradient id="soft"><stop stop-color="#527f84" stop-opacity=".7"/><stop offset=".6" stop-color="#6c9996" stop-opacity=".38"/><stop offset="1" stop-color="#6c9996" stop-opacity="0"/></radialGradient></defs>'
    for corners, color in FACES:
        if kind in ('triangles', 'quads'):
            drawing += f'<polygon points="{coords(corners)}" fill="{color}" stroke="#527b79" stroke-width="1.4"/>'
            for row in range(4):
                for col in range(4):
                    a, b, c, d = [point(corners, u/4, v/4) for u, v in ((col,row),(col+1,row),(col+1,row+1),(col,row+1))]
                    drawing += f'<polygon points="{coords((a,b,c,d))}" fill="none" stroke="#527b79" stroke-width="1"/>'
                    if kind == 'triangles':
                        drawing += f'<path d="M{a[0]} {a[1]}L{c[0]} {c[1]}" stroke="#527b79" stroke-width="1"/>'
        else:
            n = 7 if kind == 'points' else 6
            for row in range(n):
                for col in range(n):
                    x, y = point(corners, col/(n-1), row/(n-1))
                    if kind == 'points':
                        drawing += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.3" fill="#527b79"/>'
                    else:
                        drawing += f'<ellipse cx="{x:.2f}" cy="{y:.2f}" rx="15" ry="10" transform="rotate(18 {x:.2f} {y:.2f})" fill="url(#soft)"/>'
    save(kind, f'A box represented with {kind}', drawing)

print('Wrote four representation diagrams.')
