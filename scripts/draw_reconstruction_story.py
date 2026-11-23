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


for name, n in (('coarse', 6), ('fine', 32)):
    vertices = [(160 + 92*cos(2*pi*i/n), 125 + 92*sin(2*pi*i/n)) for i in range(n)]
    save(f'handle-{name}', f'Round handle approximated by {n} sides, compared with the same target circle', 320, 250,
         '<circle cx="160" cy="125" r="92" stroke="#9a7422" stroke-dasharray="6 6" stroke-width="2" fill="none"/>'
         + f'<polygon points="{points(vertices)}" fill="#5b8db8" fill-opacity=".25" stroke="#3d6e96" stroke-width="2.5"/>'
         + ''.join(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="2.5" fill="#3d6e96"/>' for x,y in vertices))


def cylinder_mesh(n):
    """The same capped cylinder and camera, with n flat side faces."""
    eye = (3/7, -6/7, 2/7)
    right = (2/5**.5, 1/5**.5, 0)
    up = (-2/(7*5**.5), 4/(7*5**.5), 15/(7*5**.5))
    light = (-.3, -.4, .8660254)
    dot = lambda a,b: sum(x*y for x,y in zip(a,b))
    def project_bar(p):
        return 160+102*dot(p,right), 151-102*dot(p,up)
    ring = [(.76*cos(2*pi*i/n), .76*sin(2*pi*i/n)) for i in range(n)]
    faces = []
    for i in range(n):
        j=(i+1)%n
        theta=2*pi*(i+.5)/n
        normal=(cos(theta),sin(theta),0)
        if dot(normal,eye)<=0:
            continue
        face=[(*ring[i],-.95),(*ring[j],-.95),(*ring[j],.95),(*ring[i],.95)]
        shade=.58+.42*max(0,dot(normal,light))
        fill='#'+''.join(f'{round(c*shade):02x}' for c in (91,141,184))
        faces.append((dot(tuple(sum(p[k] for p in face)/4 for k in range(3)),eye),face,fill))
    body='<ellipse cx="160" cy="275" rx="89" ry="13" fill="#e8e5de" opacity=".5"/>'
    for _, face, fill in sorted(faces):
        body+=f'<polygon points="{points([project_bar(p) for p in face])}" fill="{fill}" stroke="#adc3d1" stroke-width=".85" stroke-linejoin="round"/>'
    body+=f'<polygon points="{points([project_bar((*p,.95)) for p in ring])}" fill="#91b3cb" stroke="#3d6e96" stroke-width="1.2" stroke-linejoin="round"/>'
    return body


for name,n in (('coarse',6),('fine',32)):
    save(f'cylinder-mesh-{name}',f'A 3D round bar built with {n} flat faces around its side',320,300,cylinder_mesh(n))


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


from shared_cabinet_views import vector
for wire in (True,False):
    save('cabinet-wireframe' if wire else 'cabinet-rendered',
         'The shared cabinet mesh' if wire else 'One rendered view of the shared cabinet',320,300,
         vector(size=(320,300),scale=128,wire=wire))


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

save('nerf-query-example','A ray from the camera queries A in empty space, B near a blue surface, and C near a gold surface behind it',520,300,'''
<rect x="267" y="70" width="31" height="160" fill="#5b8db8" opacity=".48"/>
<rect x="409" y="70" width="31" height="160" fill="#dbb555" opacity=".52"/>
<path d="M66 151H485" stroke="#9a7422" stroke-width="2"/><path d="M473 143L485 151L473 159" fill="none" stroke="#9a7422" stroke-width="2"/>
<rect x="10" y="134" width="35" height="32" rx="2" fill="#f0e7d4" stroke="#9a7422" stroke-width="2"/>
<path d="M45 141L63 134V166L45 159Z" fill="#f0e7d4" stroke="#9a7422" stroke-width="2"/>
<circle cx="157" cy="151" r="6" fill="#fefdfb" stroke="#9a7422" stroke-width="2"/>
<circle cx="282" cy="151" r="6" fill="#3d6e96" stroke="white" stroke-width="2"/>
<circle cx="424" cy="151" r="6" fill="#b18b31" stroke="white" stroke-width="2"/>
<text x="157" y="114" text-anchor="middle">A</text><text x="282" y="52" text-anchor="middle">B</text><text x="424" y="52" text-anchor="middle">C</text>
<text x="5" y="207">Camera</text><text x="157" y="260" text-anchor="middle">Air</text><text x="282" y="260" text-anchor="middle">Blue front</text><text x="424" y="260" text-anchor="middle">Gold behind</text>
''')
for raised in (False, True):
    front = '''<defs>
<linearGradient id="metal"><stop stop-color="#746a52"/><stop offset=".35" stop-color="#eee1b4"/><stop offset=".65" stop-color="#b6a575"/><stop offset="1" stop-color="#796b4e"/></linearGradient>
</defs>
<text x="160" y="27" text-anchor="middle">Front view</text>
<rect x="35" y="46" width="250" height="142" fill="#5b8db8" stroke="#3d6e96" stroke-width="2"/>
<rect x="154" y="69" width="20" height="105" rx="8" fill="#24465b" opacity=".25"/>
<rect x="145" y="64" width="30" height="16" rx="3" fill="#b6a575"/>
<rect x="145" y="156" width="30" height="16" rx="3" fill="#b6a575"/>
<rect x="149" y="68" width="22" height="100" rx="9" fill="url(#metal)" stroke="#796b4e" stroke-width="1"/>
<text x="160" y="235" text-anchor="middle">Side view</text>
<rect x="70" y="256" width="18" height="150" fill="#5b8db8" stroke="#3d6e96" stroke-width="2"/>
'''
    if raised:
        side = '''<path d="M89 279H193Q203 279 203 289V373Q203 383 193 383H89V365H185V297H89Z" fill="#c4b383" stroke="#796b4e" stroke-width="2"/>
<path d="M101 333H174M107 328L101 333L107 338M168 328L174 333L168 338" fill="none" stroke="#9a7422" stroke-width="2"/>
<text x="137" y="322" text-anchor="middle" style="font-size:22px">Gap</text>
<path d="M137 350L137 418" stroke="#9a7422" stroke-width="1.5" stroke-dasharray="4 4"/>
<text x="160" y="447" text-anchor="middle">Room for fingers</text>'''
    else:
        side = '''<path d="M90 279V383" stroke="#c4b383" stroke-width="3"/>
<path d="M96 331H144" stroke="#9a7422" stroke-width="1.5"/>
<circle cx="94" cy="331" r="3" fill="#9a7422"/>
<text x="154" y="339">No gap</text>
<text x="160" y="447" text-anchor="middle">Only surface color</text>'''
    save('handle-raised' if raised else 'handle-painted',
         'Front and side views: a modeled handle projects from the panel and leaves a gap for fingers' if raised else 'Front and side views: a handle printed on the panel has no depth or gap',
         320, 460, front + side)

print('Wrote eleven reconstruction-story diagrams.')
