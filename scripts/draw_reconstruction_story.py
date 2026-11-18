#!/usr/bin/env python3
"""Original schematic geometry, projection, and ray-sampling examples."""
from html import escape
from math import cos, sin, pi, exp
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'book/assets/diagrams'
OUT.mkdir(parents=True, exist_ok=True)


def save(name, title, width, height, body):
    (OUT / f'{name}.svg').write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">'
        f'<title>{escape(title)}</title><style>text{{font-family:Arial,sans-serif;font-size:24px;fill:#333b3a}}</style>'
        + body + '</svg>\n')


def points(coords):
    return ' '.join(f'{x:.3f},{y:.3f}' for x, y in coords)








def project(x, y, z):
    return (140+130*x+63*y, 270-132*z-36*y)


def box(x0,x1,y0,y1,z0,z1,color,wire):
    faces = [
        [(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)],
        [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
        [(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)],
    ]
    body = ''
    for face, shade in zip(faces, (.78,1.12,1)):
        rgb=tuple(int(color[i:i+2],16) for i in (1,3,5))
        fill='white' if wire else '#'+''.join(f'{min(255,round(c*shade)):02x}' for c in rgb)
        pts=[project(*v) for v in face]
        body+=f'<polygon points="{points(pts)}" fill="{fill}" stroke="{"#6c9996" if wire else fill}" stroke-width="1.1"/>'
        if wire:
            body+=f'<path d="M{pts[0][0]:.3f} {pts[0][1]:.3f}L{pts[2][0]:.3f} {pts[2][1]:.3f}" stroke="#6c9996" stroke-width=".9"/>'
    return body


for wire in (True,False):
    body='<path d="M44 274L181 286L270 248L134 230Z" fill="#e8e5de" opacity=".55"/>'
    body+=box(-.5,.5,0,.72,0,1.6,'#6c9996',wire)
    body+=box(-.45,.45,-.035,0,.17,1.02,'#dbb555',wire)
    body+=box(-.45,.45,-.04,0,1.07,1.43,'#5b8db8',wire)
    body+=box(-.19,.19,-.10,-.04,1.22,1.26,'#d1d4cb',wire)
    body+=box(.30,.34,-.10,-.035,.55,.76,'#e3cd85',wire)
    save('cabinet-wireframe' if wire else 'cabinet-rendered',
         'The same cabinet geometry shown as triangle meshes' if wire else 'A shaded view of the cabinet geometry with colored surfaces',320,300,body)


save('gaussian-projection-side','A side view of two equally tall Gaussians projecting to different footprints on a virtual image plane',520,310,'''
<path d="M170 88V261" stroke="#b8ad96" stroke-width="4"/>
<path d="M40 175L450 120M40 175L450 230" stroke="#dbb555" stroke-width="1.8" stroke-dasharray="5 5" fill="none"/>
<path d="M40 175L300 120M40 175L300 230" stroke="#5b8db8" stroke-width="1.8" fill="none"/>
<path d="M40 175H490" stroke="#656158" stroke-width="1.3" stroke-dasharray="4 6"/>
<ellipse cx="450" cy="175" rx="35" ry="55" fill="#dbb555" fill-opacity=".3" stroke="#b18b31" stroke-width="2"/>
<ellipse cx="450" cy="175" rx="13" ry="55" fill="none" stroke="#b18b31" stroke-width="1.2"/>
<ellipse cx="300" cy="175" rx="35" ry="55" fill="#5b8db8" fill-opacity=".3" stroke="#3d6e96" stroke-width="2"/>
<ellipse cx="300" cy="175" rx="13" ry="55" fill="none" stroke="#3d6e96" stroke-width="1.2"/>
<path d="M170 147.5V202.5" stroke="#5b8db8" stroke-width="14" stroke-opacity=".55"/>
<path d="M170 157.561V192.439" stroke="#dbb555" stroke-width="6"/>
<circle cx="40" cy="175" r="7" fill="#9a7422"/>
<path d="M40 193V251" stroke="#656158" stroke-width="1.3"/>
<text x="4" y="282">Camera</text><text x="137" y="65">Image</text><text x="272" y="86">Near</text><text x="430" y="86">Far</text>
''')


def gaussian_gradient(name,color):
    return f'<radialGradient id="{name}">' + ''.join(
        f'<stop offset="{i/20:.2f}" stop-color="{color}" stop-opacity="{exp(-4.5*(i/20)**2):.5f}"/>'
        for i in range(21)) + f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'


save('gaussian-projected-image','Two soft projected ellipses overlap at a marked pixel, with the blue contribution in front of the gold',320,260,
     '<defs>'+gaussian_gradient('blue','#5b8db8')+gaussian_gradient('gold','#dbb555')+'</defs>'
     + '<rect x="20" y="20" width="280" height="200" fill="white" stroke="#e8e5de" stroke-width="1.5"/>'
     + '<ellipse cx="160" cy="120" rx="69" ry="53" fill="url(#gold)" opacity=".8"/>'
     + '<ellipse cx="160" cy="120" rx="109" ry="84" fill="url(#blue)" opacity=".25"/>'
     + '<circle cx="160" cy="120" r="7" fill="none" stroke="white" stroke-width="4"/><circle cx="160" cy="120" r="7" fill="none" stroke="#333b3a" stroke-width="1.5"/>'
     + '<path d="M160 131V214" stroke="#656158" stroke-width="1.2"/><text x="160" y="247" text-anchor="middle">One pixel</text>')


print('Wrote four reconstruction-story diagrams.')
