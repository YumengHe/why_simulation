#!/usr/bin/env python3
"""Original cabinet illustrations of SfM and Gaussian fitting.

Camera rays and all projected views use one 3D cabinet. The sparse points and
early/late parameter sets are constructed teaching stages, not SfM/training
outputs. Rendered cabinet views stand in for reference photographs.
"""
from pathlib import Path
import json
import math
import re
import numpy as np
from PIL import Image, ImageDraw

from animate_projection import font
from animate_gaussian_cabinet import CENTERS, COVS, COLORS, GROUPS, NAMES, View, camera, project, blend_splats, U, V

OUT = Path(__file__).resolve().parents[1] / 'book/assets/gaussian-learning'
INK, GOLD, CORAL = '#313a37', '#9a7422', '#bf644b'
SIZE = (420, 430)
POINT_A = np.array([-.51, -.49, .74])


def sparse_samples():
    """A reproducible illustrative sample, with a recognizable front silhouette."""
    rng = np.random.default_rng(18)
    indices = list(rng.choice(len(CENTERS), 135, replace=False))
    for group in ('drawer', 'door'):
        ids = np.flatnonzero(GROUPS == group)
        indices.extend(rng.choice(ids, min(25, len(ids)), replace=False))
    handle_ids = np.flatnonzero(np.char.find(NAMES.astype(str), 'handle') >= 0)
    indices.extend(rng.choice(handle_ids, min(35, len(handle_ids)), replace=False))
    ids = np.unique(indices)
    return np.vstack([CENTERS[ids], POINT_A]), np.vstack([COLORS[ids], [91,141,184]])


SPARSE, SPARSE_COLORS = sparse_samples()
INITIAL_COVS = np.repeat((np.eye(3)*.085**2)[None], len(SPARSE), axis=0)


def render(means, covs, colors, angle=20, opacity=.94, size=SIZE):
    w,h=size
    uv,cov,depth=project(means,covs,angle)
    scale=np.diag([w/(2*U),-h/(2*V)])
    return blend_splats(uv@scale.T+[w/2,h/2],scale@cov@scale.T,colors,depth,w,h,opacity).convert('RGB')


def mark_a(im,angle):
    w,h=im.size
    uv,_,_=project(POINT_A[None],np.eye(3)[None],angle)
    x,y=uv[0]*[w/(2*U),-h/(2*V)]+[w/2,h/2]
    d=ImageDraw.Draw(im)
    d.ellipse((x-6,y-6,x+6,y+6),fill=CORAL,outline='white',width=2)
    d.line((x-5,y-6,x-31,y-37),fill=CORAL,width=2)
    d.text((x-36,y-45),'A',font=font(25,True),anchor='mm',fill=CORAL)


def cloud(blobs=False):
    im=Image.new('RGB',SIZE,'white');d=ImageDraw.Draw(im)
    view=View(170,(0,0,0),(210,210),20,14)
    points=view(SPARSE)
    if blobs:
        cov=view.matrix@INITIAL_COVS@view.matrix.T
        depth=-(SPARSE@view.eye)
        im=blend_splats(points,cov,SPARSE_COLORS,depth,*SIZE,.46).convert('RGB')
        d=ImageDraw.Draw(im)
        # A few outlined ellipsoid guides show size; these are not hard edges.
        for i in np.argsort(SPARSE[:,1])[:22]:
            x,y=points[i];r=170*.085
            d.ellipse((x-r,y-r,x+r,y+r),outline=tuple((SPARSE_COLORS[i]*.83).astype(int)),width=1)
    else:
        for i in np.argsort(SPARSE@view.eye):
            x,y=points[i]
            d.ellipse((x-2.5,y-2.5,x+2.5,y+2.5),fill=tuple(SPARSE_COLORS[i].astype(int)))
    x,y=view(POINT_A)
    d.ellipse((x-6,y-6,x+6,y+6),fill=CORAL,outline='white',width=2)
    d.text((x-21,y-17),'A',font=font(24,True),fill=CORAL,anchor='mm')
    return im


def triangulation():
    im=Image.new('RGB',(840,650),'white');d=ImageDraw.Draw(im)
    view=View(128,(0,-1.25,0),(420,322),12,48)
    # The faint outline supplies context; only A is triangulated in this sketch.
    corners=np.array([[x,y,z] for x in (-.62,.62) for y in (-.43,.43) for z in (-.86,.86)])
    for i in range(8):
        for j in range(i+1,8):
            if np.count_nonzero(corners[i]!=corners[j])==1:
                d.line([tuple(p) for p in view(corners[[i,j]])],fill='#d6dfdb',width=3)
    for z0,z1,col in [(.33,.74,'#8cacc5'),(-.73,.26,'#c9b26d')]:
        panel=np.array([[-.51,-.49,z0],[.51,-.49,z0],[.51,-.49,z1],[-.51,-.49,z1],[-.51,-.49,z0]])
        d.line([tuple(p) for p in view(panel)],fill=col,width=3)
    for angle,name in [(-35,'Camera 1'),(35,'Camera 3')]:
        c,f,r,u=camera(angle)
        p=view(c);a=view(POINT_A)
        d.line([tuple(p),tuple(a)],fill=CORAL,width=3)
        # Small 3D image plane, intersected by the correct camera ray.
        hit=c+.95*(POINT_A-c)/np.linalg.norm(POINT_A-c)
        plane=np.array([hit+x*r+y*u for x,y in [(-.19,-.14),(.19,-.14),(.19,.14),(-.19,.14)]])
        poly=view(plane)
        d.polygon([tuple(q) for q in poly],fill='#f8eee8',outline=CORAL,width=2)
        h=view(hit);d.ellipse((h[0]-5,h[1]-5,h[0]+5,h[1]+5),fill=CORAL)
        x,y=p;d.rounded_rectangle((x-21,y-14,x+21,y+14),radius=3,fill='#797f77')
        d.ellipse((x-7,y-7,x+7,y+7),fill='#c5ccc4')
        d.text((x,y+37),name,font=font(25),fill=INK,anchor='mm')
    x,y=view(POINT_A)
    d.ellipse((x-8,y-8,x+8,y+8),fill=CORAL,outline='white',width=2)
    d.text((x-21,y-29),'A',font=font(29,True),fill=CORAL,anchor='mm')
    d.text((420,50),'Two views locate the same corner',font=font(29,True),fill=INK,anchor='mm')
    d.text((420,590),'The lines meet at an estimated 3D point.',font=font(25),fill=INK,anchor='mm')
    return im


def operation_svg(kind):
    common='''<svg xmlns="http://www.w3.org/2000/svg" width="420" height="230" viewBox="0 0 420 230"><defs><radialGradient id="b"><stop stop-color="#5b8db8" stop-opacity=".9"/><stop offset="1" stop-color="#5b8db8" stop-opacity="0"/></radialGradient><radialGradient id="f"><stop stop-color="#5b8db8" stop-opacity=".12"/><stop offset="1" stop-color="#5b8db8" stop-opacity="0"/></radialGradient><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#9a7422"/></marker></defs><rect width="420" height="230" fill="white"/><g font-family="Arial,sans-serif" font-size="19" fill="#313a37" text-anchor="middle"><text x="95" y="31">Before</text><text x="325" y="31">After</text></g><path d="M184 115 H230" stroke="#9a7422" stroke-width="2" marker-end="url(#a)"/>'''
    if kind=='adjust':
        body='''<path d="M30 153 H160 M260 153 H390" stroke="#c7d6de" stroke-dasharray="5 5"/><ellipse cx="90" cy="111" rx="58" ry="40" fill="url(#b)" transform="rotate(-25 90 111)"/><ellipse cx="325" cy="149" rx="70" ry="17" fill="url(#b)"/><path d="M300 106 L320 132" stroke="#9a7422" marker-end="url(#a)"/><text x="210" y="210" text-anchor="middle" font-family="Arial,sans-serif" font-size="19" fill="#313a37">Move and flatten near a panel</text>'''
    elif kind=='add':
        body='''<ellipse cx="95" cy="116" rx="75" ry="52" fill="url(#b)"/><ellipse cx="296" cy="113" rx="38" ry="23" fill="url(#b)" transform="rotate(-25 296 113)"/><ellipse cx="352" cy="122" rx="38" ry="23" fill="url(#b)" transform="rotate(20 352 122)"/><text x="210" y="210" text-anchor="middle" font-family="Arial,sans-serif" font-size="19" fill="#313a37">Split one large blob into smaller ones</text>'''
    else:
        body='''<ellipse cx="75" cy="127" rx="47" ry="31" fill="url(#b)"/><ellipse cx="140" cy="84" rx="34" ry="30" fill="url(#f)"/><ellipse cx="75" cy="127" rx="47" ry="31" fill="none" stroke="#a8c2d5" stroke-width=".7"/><ellipse cx="315" cy="127" rx="47" ry="31" fill="url(#b)"/><circle cx="140" cy="84" r="31" fill="none" stroke="#bf644b" stroke-dasharray="4 4"/><text x="210" y="210" text-anchor="middle" font-family="Arial,sans-serif" font-size="19" fill="#313a37">Discard a nearly transparent blob</text>'''
    # The HTML caption explains the operation; avoid tiny duplicate text here.
    body=re.sub(r'<text[^>]*>.*?</text>', '', body)
    return (common+body+'</svg>').replace('font-size="19"','font-size="25"')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for name,angle in [('left',-35),('front',0),('right',35)]:
        im=render(CENTERS,COVS,COLORS,angle,size=(420,500));mark_a(im,angle)
        im.save(OUT/f'reference-{name}.png')
    cloud().save(OUT/'sparse-points.png')
    cloud(True).save(OUT/'initial-blobs.png')
    triangulation().save(OUT/'triangulation.png')
    render(SPARSE,INITIAL_COVS,SPARSE_COLORS,opacity=.46).save(OUT/'early-render.png')
    # The final rendering uses the established analytic cabinet, not fitted data.
    render(CENTERS,COVS,COLORS).save(OUT/'later-render.png')
    render(CENTERS,COVS,COLORS,-15).save(OUT/'new-view.png')
    for kind in ['adjust','add','remove']:(OUT/f'update-{kind}.svg').write_text(operation_svg(kind))
    # Check that the rays hit the same A and screen projections are finite.
    for angle in (-35,0,35):
        uv,_,depth=project(POINT_A[None],np.eye(3)[None],angle)
        c,f,r,u=camera(angle)
        ray=f+uv[0,0]/1.3*r+uv[0,1]/1.3*u
        assert np.allclose(c+depth[0]*ray,POINT_A)
    assert len(SPARSE)<len(CENTERS)
    assert np.all(np.linalg.eigvalsh(INITIAL_COVS)>0)
    (OUT/'manifest.json').write_text(json.dumps({
        'geometry_source':'scripts/shared_cabinet.py',
        'provenance':'Original analytic teaching cabinet. Rendered views illustrate photographs. Sparse points and parameter stages are constructed, not recovered or optimized.',
        'initial_blob_count':len(SPARSE),'later_blob_count':len(CENTERS),
        'corner_A':POINT_A.tolist(),'camera_angles':[-35,0,35],
        'rendering':'Same perspective projection and depth-sorted Gaussian alpha blending as the cabinet video.',
        'references':['https://colmap.github.io/tutorial.html','https://arxiv.org/html/2308.04079v1']
    },indent=2)+'\n')
    print(f'Created cabinet fitting illustrations: {len(SPARSE)} sparse samples; {len(CENTERS)} final illustrative blobs. Projection checks passed.')


if __name__=='__main__':main()
