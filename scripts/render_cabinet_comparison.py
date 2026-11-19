#!/usr/bin/env python3
"""Render a scripted cabinet as a 2D reference, a mesh, and Gaussians.

Explicit box geometry and a fixed camera produce every pixel. This illustrates
representations, not inference by TRELLIS or any image-generation system.
"""
from pathlib import Path
import json

import numpy as np
from PIL import Image

from animate_gaussian_cabinet import camera, camera_image, FOCAL, U, V
from draw_cabinet_mesh_detail import Mesh

OUT = Path(__file__).resolve().parents[1] / 'book/assets/examples/cabinet-representations'
W, H, SS = 528, 700, 2


def cabinet():
    mesh = Mesh()
    teal, blue, gold = (108,153,150), (91,141,184), (219,181,85)
    boxes = [
        ((-.62,-.43,-.86),(-.54,.43,.86),teal),
        ((.54,-.43,-.86),(.62,.43,.86),teal),
        ((-.54,.35,-.86),(.54,.43,.86),teal),
        ((-.54,-.43,.79),(.54,.35,.86),teal),
        ((-.54,-.43,-.86),(.54,.35,-.78),teal),
        ((-.51,-.49,.33),(.51,-.43,.74),blue),
        ((-.51,-.485,-.73),(.51,-.43,.26),gold),
        ((-.24,-.585,.515),(.24,-.55,.555),(204,210,204)),
        ((.345,-.57,-.35),(.385,-.535,-.10),(174,136,51)),
    ]
    for x in (-.24,.205):
        boxes.append(((x,-.56,.515),(x+.035,-.49,.555),(185,196,192)))
    for z in (-.35,-.135):
        boxes.append(((.345,-.55,z),(.385,-.485,z+.035),(174,136,51)))
    for lo, hi, color in boxes:
        mesh.box(lo, hi, color)
    return mesh


def render_mesh(mesh, angle, wire=False):
    """Perspective triangle rasterization with reciprocal-depth visibility."""
    width, height = W*SS, H*SS
    image = np.full((height,width,3),255.,dtype=np.float32)
    nearest = np.full((height,width),-np.inf)
    center, forward, right, up = camera(angle)
    for tri, color in zip(mesh.triangles,mesh.colors):
        normal = np.cross(tri[1]-tri[0],tri[2]-tri[0])
        normal /= np.linalg.norm(normal)
        if normal @ (center-tri.mean(axis=0)) <= 0:
            continue
        q = tri-center
        depth = q @ forward
        assert np.all(depth > 0)
        uv = FOCAL*np.column_stack([q@right,q@up])/depth[:,None]
        pts = uv*np.array([width/(2*U),-height/(2*V)])+[width/2,height/2]
        x0,y0 = np.maximum(np.floor(pts.min(axis=0)).astype(int),0)
        x1,y1 = np.minimum(np.ceil(pts.max(axis=0)).astype(int)+1,[width,height])
        if x0>=x1 or y0>=y1:
            continue
        yy,xx = np.mgrid[y0:y1,x0:x1]; xx=xx+.5; yy=yy+.5
        a,b,c = pts
        den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-10:
            continue
        wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
        wc=1-wa-wb
        invdepth=wa/depth[0]+wb/depth[1]+wc/depth[2]
        old=nearest[y0:y1,x0:x1]
        visible=(wa>=0)&(wb>=0)&(wc>=0)&(invdepth>old)
        # Match the face palette used by the Gaussian teaching cabinet.
        axis=int(np.argmax(np.abs(normal))); side=int(normal[axis]>0)
        shade=[(.83,.74),(1.,.79),(.68,1.08)][axis][side]
        rgb=np.clip(np.array(color)*shade,0,255)
        patch=image[y0:y1,x0:x1]; patch[visible]=rgb
        if wire:
            alt=np.array([abs(den)/np.linalg.norm(b-c),abs(den)/np.linalg.norm(c-a),abs(den)/np.linalg.norm(a-b)])
            edge=np.minimum.reduce([wa*alt[0],wb*alt[1],wc*alt[2]])<.75*SS
            patch[visible&edge]=rgb*.63
        old[visible]=invdepth[visible]
    return Image.fromarray(image.astype(np.uint8)).resize((W,H),Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    mesh=cabinet()
    assert len(mesh.triangles)==156
    render_mesh(mesh,0).save(OUT/'reference.png')
    render_mesh(mesh,24,wire=True).save(OUT/'mesh.png')
    camera_image(24,W*SS,H*SS).convert('RGB').resize((W,H),Image.Resampling.LANCZOS).save(OUT/'gaussians.png')
    (OUT/'manifest.json').write_text(json.dumps({
        'generator':'scripts/render_cabinet_comparison.py',
        'source':'Explicit cabinet geometry, with the same box layout and colors as animate_gaussian_cabinet.py.',
        'reference':'A front-view mesh render, not a photograph or image-model output.',
        'comparison':'Mesh and Gaussian representations use the same camera (24 degrees), lens, dimensions, and face colors.',
        'limitation':'Scripted teaching representations; not TRELLIS predictions or learned reconstruction results.',
        'size':[W,H],'mesh_triangles':len(mesh.triangles)
    },indent=2)+'\n')
    print('Rendered three cabinet representation views from explicit geometry.')


if __name__=='__main__':
    main()
