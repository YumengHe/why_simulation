#!/usr/bin/env python3
"""Original vector teaching views of one cabinet, with a fixed camera.

Dots, mesh faces, and soft marks illustrate data layouts; no learned
reconstruction is claimed. The field view marks sample queries only.
"""
from pathlib import Path
from math import ceil, sqrt

OUT=Path(__file__).resolve().parents[1]/'book/assets/diagrams'
TEAL,BLUE,GOLD='#6c9996','#5b8db8','#dbb555'
BOXES=[((-.62,-.43,-.86),(-.54,.43,.86),TEAL),((.54,-.43,-.86),(.62,.43,.86),TEAL),
       ((-.54,.35,-.86),(.54,.43,.86),TEAL),((-.54,-.43,.79),(.54,.35,.86),TEAL),
       ((-.54,-.43,-.86),(.54,.35,-.78),TEAL),((-.51,-.49,.33),(.51,-.43,.74),BLUE),
       ((-.51,-.485,-.73),(.51,-.43,.26),GOLD),((-.24,-.59,.515),(.24,-.55,.555),'#d2d8d1'),
       ((.345,-.58,-.35),(.385,-.535,-.10),'#ad8736')]
E=(3/7,-6/7,2/7); R=(2/sqrt(5),1/sqrt(5),0)
U=(E[1]*R[2]-E[2]*R[1], E[2]*R[0]-E[0]*R[2], E[0]*R[1]-E[1]*R[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def project(p):return (170+130*dot(p,R),165-130*dot(p,U))
def points(vs):return ' '.join(f'{x:.2f},{y:.2f}' for x,y in map(project,vs))
def blend(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
faces=[]
for lo,hi,color in BOXES:
    for axis,side in [(0,1),(1,0),(2,1)]:
        axes=[i for i in range(3) if i!=axis]
        v=[]
        for s,t in [(0,0),(1,0),(1,1),(0,1)]:
            p=[0.,0.,0.];p[axis]=(lo,hi)[side][axis];p[axes[0]]=(lo,hi)[s][axes[0]];p[axes[1]]=(lo,hi)[t][axes[1]];v.append(tuple(p))
        faces.append((v,color,axis))
faces.sort(key=lambda f:sum(dot(p,E) for p in f[0])/4)

def surface(v,u,t):return blend(blend(v[0],v[1],u),blend(v[3],v[2],u),t)
def image(mode):
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="340" height="320" viewBox="0 0 340 320" role="img">',
         f'<title>A cabinet represented as {mode}</title>','<rect width="340" height="320" fill="#fefdfb"/>']
    for i,(v,col,axis) in enumerate(faces):
        a=sqrt(sum((x-y)**2 for x,y in zip(v[0],v[1])));b=sqrt(sum((x-y)**2 for x,y in zip(v[0],v[3])))
        n=max(1,ceil(a/.24));m=max(1,ceil(b/.24))
        if mode in ('quads','triangles','field'):
            opacity='.16' if mode=='field' else '.9'
            svg.append(f'<polygon points="{points(v)}" fill="{col}" fill-opacity="{opacity}" stroke="#41554f" stroke-opacity="{opacity}" stroke-width="1.2"/>')
        if mode in ('quads','triangles'):
            for j in range(n):
                for k in range(m):
                    q=[surface(v,x/n,y/m) for x,y in [(j,k),(j+1,k),(j+1,k+1),(j,k+1)]]
                    svg.append(f'<polygon points="{points(q)}" fill="none" stroke="#405752" stroke-width=".6"/>')
                    if mode=='triangles':
                        xy=points([q[0],q[2]])
                        svg.append(f'<polyline points="{xy}" fill="none" stroke="#405752" stroke-width=".6"/>')
        if mode in ('points','gaussians'):
            n=max(1,ceil(a/.11));m=max(1,ceil(b/.11))
            if mode=='gaussians':
                svg.append(f'<defs><radialGradient id="g{i}"><stop stop-color="{col}" stop-opacity=".85"/><stop offset=".6" stop-color="{col}" stop-opacity=".36"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient></defs>')
            for j in range(n):
                for k in range(m):
                    p=surface(v,(j+.5)/n,(k+.5)/m);x,y=project(p)
                    if mode=='points':svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="1.7" fill="{col}"/>')
                    else:svg.append(f'<ellipse cx="{x:.2f}" cy="{y:.2f}" rx="10" ry="7" fill="url(#g{i})"/>')
    if mode=='field':
        for p,col in [((0,-.49,.55),BLUE),((0,-.485,-.4),GOLD),((.62,0,.2),TEAL)]:
            x,y=project(p)
            svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="{col}" stroke="white" stroke-width="2"/>')
        svg.append('<rect x="29" y="282" width="282" height="29" rx="3" fill="#f9f8f5" stroke="#e8e5de"/><text x="170" y="302" text-anchor="middle" fill="#313a37" font-family="Arial,sans-serif" font-size="15">Query a position → color + density</text>')
    return ''.join(svg)+'</svg>\n'
for mode in ['points','quads','triangles','gaussians','field']:
    (OUT/f'cabinet-representation-{mode}.svg').write_text(image(mode))
print('Created five cabinet representation diagrams.')
