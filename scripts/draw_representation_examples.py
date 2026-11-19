#!/usr/bin/env python3
"""Draw original, static teaching examples for the 3D representation chapter."""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'book/assets/diagrams'
OUT.mkdir(parents=True, exist_ok=True)


def save(name, title, width, height, body):
    (OUT / f'{name}.svg').write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">'
        f'<title>{escape(title)}</title>'
        '<style>text{font-family:Arial,sans-serif;fill:#333b3a;font-size:24px}</style>'
        + body + '</svg>\n'
    )


save('mesh-parts', 'One corner is a vertex, one connecting line is an edge, and the filled area is a face', 520, 280, '''
<path d="M90 80H340V220H90Z" fill="#dbe7ed" stroke="#5b8db8" stroke-width="3"/>
<path d="M90 80H340" stroke="#9a7422" stroke-width="6"/>
<circle cx="90" cy="80" r="7" fill="#9a7422" stroke="#fefdfb" stroke-width="2"/>
<circle cx="340" cy="80" r="5" fill="#5b8db8"/><circle cx="340" cy="220" r="5" fill="#5b8db8"/><circle cx="90" cy="220" r="5" fill="#5b8db8"/>
<path d="M60 46L84 73M224 44V72M220 153H388" stroke="#656158" stroke-width="1.5" fill="none"/><circle cx="220" cy="153" r="3" fill="#656158"/>
<text x="8" y="31">Vertex</text><text x="198" y="31">Edge</text><text x="399" y="161">Face</text>
''')

for triangulated in (True, False):
    body = '<path d="M48 45H265V178H48Z" fill="#dbe7ed" stroke="#5b8db8" stroke-width="2.5"/>'
    if triangulated:
        body += '<path d="M48 45H265V178Z" fill="#a6c2d8"/><path d="M48 45L265 178" stroke="#5b8db8" stroke-width="2.5"/>'
    for x, y in ((48,45),(265,45),(265,178),(48,178)):
        body += f'<circle cx="{x}" cy="{y}" r="5" fill="#3d6e96"/>'
    body += '<text x="24" y="38">A</text><text x="274" y="38">B</text><text x="274" y="202">C</text><text x="24" y="202">D</text>'
    save('mesh-two-triangles' if triangulated else 'mesh-one-quad',
         'The same four corners connected as two triangular faces' if triangulated else 'The same four corners connected as one four-sided face',
         320, 225, body)

for name, opacity in (('low', .25), ('high', .85)):
    body = '''<defs><radialGradient id="splat"><stop stop-color="#3b76a4"/><stop offset=".4" stop-color="#3b76a4" stop-opacity=".8"/><stop offset="1" stop-color="#3b76a4" stop-opacity="0"/></radialGradient></defs>
<rect x="20" y="20" width="280" height="180" fill="#f9f8f5"/>'''
    for x in range(40, 300, 40):
        body += f'<path d="M{x} 20V200" stroke="#c7c3b9" stroke-width="2"/>'
    for y in range(40, 200, 40):
        body += f'<path d="M20 {y}H300" stroke="#c7c3b9" stroke-width="2"/>'
    body += f'<ellipse cx="160" cy="110" rx="125" ry="75" transform="rotate(-15 160 110)" fill="url(#splat)" opacity="{opacity}"/>'
    save(f'gaussian-opacity-{name}', f'A projected Gaussian with {name} opacity over the same background grid', 320, 220, body)

save('nerf-ray-example', 'A camera ray is sampled in empty space, near a blue front panel, and behind the panel to calculate one pixel', 520, 350, '''
<defs><marker id="ray-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7Z" fill="#9a7422"/></marker></defs>
<rect x="288" y="42" width="32" height="170" rx="2" fill="#a6c2d8"/>
<text x="304" y="28" text-anchor="middle">Blue panel</text>
<rect x="18" y="106" width="43" height="34" rx="3" fill="#f0e7d4" stroke="#9a7422" stroke-width="2"/>
<path d="M61 113L79 105V141L61 133Z" fill="#f0e7d4" stroke="#9a7422" stroke-width="2"/>
<path d="M81 123H487" stroke="#9a7422" stroke-width="2" marker-end="url(#ray-arrow)"/>
<g fill="#fefdfb" stroke="#9a7422" stroke-width="2"><circle cx="141" cy="123" r="6"/><circle cx="200" cy="123" r="6"/><circle cx="257" cy="123" r="6"/></g>
<g fill="#5b8db8" stroke="#fefdfb" stroke-width="2"><circle cx="295" cy="123" r="6"/><circle cx="306" cy="123" r="6"/></g>
<g fill="#fefdfb" stroke="#9a7422" stroke-width="2"><circle cx="374" cy="123" r="6"/><circle cx="432" cy="123" r="6"/></g>
<text x="7" y="176">Camera</text><text x="179" y="83">Air</text><text x="354" y="176">Behind</text>
<path d="M141 220V233H432V220M287 233V265" stroke="#656158" stroke-width="1.5" fill="none"/>
<text x="80" y="297">Combine samples</text><path d="M303 289H345" stroke="#9a7422" stroke-width="2" marker-end="url(#ray-arrow)"/>
<rect x="366" y="270" width="37" height="37" fill="#5b8db8"/><text x="417" y="297">Pixel</text>
''')

for hollow in (False, True):
    body = ''
    if hollow:
        body += '<path d="M48 30H272V203H249V53H71V203H48Z" fill="#a9c5c0" stroke="#6c9996" stroke-width="2"/>'
    else:
        body += '<rect x="48" y="30" width="224" height="173" fill="#a9c5c0" stroke="#6c9996" stroke-width="2"/>'
    body += '<rect x="88" y="74" width="144" height="116" rx="2" fill="#5b8db8" fill-opacity=".32" stroke="#3d6e96" stroke-width="3"/><path d="M89 182H231" stroke="#3d6e96" stroke-width="8"/>'
    body += '<path d="M160 155V240M150 227L160 240L170 227" fill="none" stroke="#9a7422" stroke-width="3"/>'
    if not hollow:
        body += '<path d="M139 109L181 151M181 109L139 151" stroke="#aa5146" stroke-width="4"/>'
    save('collision-hollow' if hollow else 'collision-filled',
         'Top view: cabinet collision walls leave space around the drawer' if hollow else 'Top view: one solid collision box overlaps the drawer',
         320, 260, body)

print('Wrote eight original teaching diagrams.')
