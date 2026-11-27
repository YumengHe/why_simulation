#!/usr/bin/env python3
"""Analytic CAD teaching plates using the canonical handle; no CAD kernel run."""
from pathlib import Path
from types import SimpleNamespace
import json, math
import numpy as np
from PIL import ImageDraw
from shared_cabinet import mesh, PART_BY_NAME, part_triangles
from preview_shared_cabinet import render
from draw_dust3r_examples import label
OUT=Path(__file__).resolve().parents[1]/'book/assets/cad'
GRIP=PART_BY_NAME['drawer-handle-grip']
R=GRIP['radius']; L=np.linalg.norm(np.array(GRIP['end'])-GRIP['start'])
INK='#293632'; BLUE='#447ca4'; GOLD='#aa7c25'
def svg(name,b):
    (OUT/name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="420" viewBox="0 0 600 420"><rect width="600" height="420" fill="#fefdfb"/><g font-family="Arial, sans-serif" fill="{INK}">{b}</g></svg>')
def txt(x,y,s,size=22,color=INK):return f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" fill="{color}">{s}</text>'
def line(a,b,color=BLUE):return f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" fill="none" stroke="{color}" stroke-width="2"/>'
def cross_section(n=None):
    b=txt(300,38,'A circular cross-section' if n is None else f'{n} samples around the circle',26)
    b+='<circle cx="300" cy="210" r="115" fill="none" stroke="#aa7c25" stroke-width="2"/>'
    if n:
        u=np.arange(n)*2*math.pi/n;p=np.column_stack([300+115*np.cos(u),210-115*np.sin(u)])
        b+='<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in p)+'" fill="#e5edf1" fill-opacity="0.7" stroke="#447ca4" stroke-width="2"/>'
        for x,y in p:b+=f'<circle cx="{x}" cy="{y}" r="3.5" fill="{BLUE}"/>'
        b+=txt(300,365,f'Max. radial gap: {R*(1-math.cos(math.pi/n))*1000:.2f} mm',23)
        b+=txt(300,397,'Gold: circle   Blue: mesh cross-section',19)
    else:
        b+=line((300,210),(415,210))+txt(356,198,'r',24,BLUE)
        b+=line((300,210),(381.32,128.68),GOLD)
        b+='<circle cx="381.32" cy="128.68" r="6" fill="#aa7c25"/><path d="M335,210 A35,35 0 0 0 324.75,185.25" fill="none" stroke="#aa7c25" stroke-width="2"/>'
        b+=txt(347,179,'u',22,GOLD)
        b+=txt(300,365,'Change the angle to locate a point.',23)+txt(300,397,'Radius r stays fixed around the circle.',19)
    svg('circle.svg' if n is None else f'section-{n}.svg',b)
def handle(n=96,r=R,edges=False):
    parts=[dict(v) for k,v in PART_BY_NAME.items() if k.startswith('drawer-handle')]
    for p in parts:
        if p['name']=='drawer-handle-grip':p['radius']=r
    tri=np.concatenate([part_triangles(p,n) for p in parts]);col=np.concatenate([np.tile(p['color'],(4*n,1)) for p in parts])
    return render(SimpleNamespace(triangles=tri,colors=col),size=(680,300),center=(0,-.57,.53),scale=1050,ss=2,edges=edges)
def surface_plot():
    eye=np.array([2.,-5.,3.]);eye/=np.linalg.norm(eye)
    right=np.cross([0,0,1],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
    def q(p):return np.array([300+900*np.dot(p,right),208-900*np.dot(p,up)])
    def S(u,v):return np.array([v-L/2,R*np.cos(u),R*np.sin(u)])
    b=txt(300,36,'Move around and along the grip',26)
    for v in np.linspace(0,L,7):
        p=[q(S(u,v)) for u in np.linspace(0,2*np.pi,129)]
        b+='<polyline points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in p)+'" fill="none" stroke="#afc2c8" stroke-width="1.3"/>'
    for u in np.linspace(0,2*np.pi,12,endpoint=False):b+=line(q(S(u,0)),q(S(u,L)),'#afc2c8')
    p=q(S(math.pi,.3));b+=f'<circle cx="{p[0]}" cy="{p[1]}" r="6" fill="{GOLD}"/>'
    b+=line(p,(380,105),GOLD)+txt(390,90,'One surface point',20,GOLD)
    b+=txt(300,342,'u: angle around    v: distance along',23)+txt(300,383,'Guide lines show selected parameter values.',18)
    svg('surface.svg',b)
    for u in np.linspace(0,2*np.pi,21):
        for v in [0,.3,L]:assert abs(np.linalg.norm(S(u,v)[1:])-R)<1e-12
    assert np.allclose(S(0,.3),S(2*np.pi,.3))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    im=render(mesh(),size=(600,590),scale=245)
    eye=np.array([3.,-6.,2.6]);eye/=np.linalg.norm(eye)
    right=np.cross([0,0,1],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
    p=np.array([0,-.65,.53])-np.array([0,-.2,0]);x=300+245*p@right;y=295-245*p@up
    d=ImageDraw.Draw(im);d.rounded_rectangle((x-70,y-27,x+70,y+27),radius=6,outline=GOLD,width=3)
    label(d,(300,560),'The same drawer handle',24,INK,True);im.save(OUT/'cabinet.png')
    for n in (8,32):handle(n,edges=True).save(OUT/f'mesh-{n}.png');cross_section(n)
    handle().save(OUT/'handle.png');handle(r=.035).save(OUT/'handle-thinner.png');cross_section();surface_plot()
    (OUT/'manifest.json').write_text(json.dumps({'generator':'scripts/draw_cad_examples.py','canonical_component':GRIP,'radius_m':R,'length_m':L,'surface_local':'S(u,v)=(v,r*cos(u),r*sin(u))','domain':'0 <= u <= 2*pi; 0 <= v <= L','local_to_world':'(x,y,z) -> (x-0.25,y-0.65,z+0.53)','display_note':'Analytic teaching geometry. Surface pictures use samples to draw pixels; no CAD kernel or reconstruction is run.','variant_radius_m':.035,'radial_error_m':{str(n):R*(1-math.cos(math.pi/n)) for n in (8,32)}},indent=2)+'\n')
    print('Generated nine CAD figures; cylinder queries verified.')
if __name__=='__main__':main()
