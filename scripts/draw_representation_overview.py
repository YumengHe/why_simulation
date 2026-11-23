#!/usr/bin/env python3
"""Five scripted representations of the canonical teaching cabinet.

Opaque depth-tested meshes share geometry with sampled points, Gaussians and
field-query illustrations. Quad and triangle figures differ only in whether
one diagonal is shown inside each surface patch. No learned result is claimed.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
from shared_cabinet import PARTS, mesh, gaussians, field, _cylinder_basis
from preview_shared_cabinet import font
from animate_gaussian_cabinet import blend_splats

OUT=Path(__file__).resolve().parents[1]/'book/assets/diagrams'
W,H=680,640
EYE=np.array([3.,-6.,2.6]);EYE/=np.linalg.norm(EYE)
RIGHT=np.cross([0,0,1],EYE);RIGHT/=np.linalg.norm(RIGHT)
UP=np.cross(EYE,RIGHT)
SCALE=260
CENTER=np.array([340.,310.])
PAPER=(254,253,251)


def project(points):
    return np.asarray(points)@np.array([RIGHT,-UP]).T*SCALE+CENTER


def patches():
    """Quad patches on all boxes and handle cylinders, outward wound."""
    result=[]
    def add(quad,color,center):
        q=np.array(quad)
        if np.cross(q[1]-q[0],q[2]-q[0])@(q.mean(axis=0)-center)<0:q=q[::-1]
        result.append((q,np.asarray(color)))
    for part in PARTS:
        if part['kind']=='box':
            lo,hi=np.asarray(part['lo']),np.asarray(part['hi']);center=(lo+hi)/2
            for axis in range(3):
                other=[d for d in range(3) if d!=axis]
                grids=[np.linspace(lo[d],hi[d],max(1,math.ceil((hi[d]-lo[d])/.24))+1) for d in other]
                for side in (lo[axis],hi[axis]):
                    for j in range(len(grids[0])-1):
                        for k in range(len(grids[1])-1):
                            quad=[]
                            for a,b in ((j,k),(j+1,k),(j+1,k+1),(j,k+1)):
                                p=np.zeros(3);p[axis]=side;p[other]=[grids[0][a],grids[1][b]];quad.append(p)
                            add(quad,part['color'],center)
        else:
            start,end,axis,u,v,length=_cylinder_basis(part);n=16;center=(start+end)/2
            ring=np.array([part['radius']*(u*math.cos(i*2*math.pi/n)+v*math.sin(i*2*math.pi/n)) for i in range(n)])
            for i in range(n):
                j=(i+1)%n;add([start+ring[i],start+ring[j],end+ring[j],end+ring[i]],part['color'],center)
            for c in (start,end):
                for i in range(0,n,2):
                    add([c,c+ring[i],c+ring[(i+1)%n],c+ring[(i+2)%n]],part['color'],center)
    return result


def raster(mode='quads', surface_patches=None):
    rgb=np.full((H,W,3),PAPER,float);zbuffer=np.full((H,W),-np.inf)
    for quad,color in (patches() if surface_patches is None else surface_patches):
        normal=np.cross(quad[1]-quad[0],quad[2]-quad[0]);normal/=np.linalg.norm(normal)
        if normal@EYE<=0:continue
        shade=np.sum(normal**2*np.where(normal>0,[.74,.79,1.08],[.83,1.,.68]))
        col=np.clip(color*shade,0,255)
        for indices,flags in [([0,1,2],[True,False,True]),([0,2,3],[True,True,False])]:
            tri=quad[indices];pts=project(tri);z=tri@EYE
            x0,y0=np.maximum(np.floor(pts.min(axis=0)).astype(int),0)
            x1,y1=np.minimum(np.ceil(pts.max(axis=0)).astype(int)+1,[W,H])
            if x0>=x1 or y0>=y1:continue
            yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5;a,b,c=pts
            den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-10:continue
            wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;wc=1-wa-wb
            depth=wa*z[0]+wb*z[1]+wc*z[2];old=zbuffer[y0:y1,x0:x1]
            visible=(wa>=-1e-9)&(wb>=-1e-9)&(wc>=-1e-9)&(depth>old-1e-12)
            patch=rgb[y0:y1,x0:x1];patch[visible]=col
            if mode in ('quads','triangles'):
                alt=np.array([abs(den)/np.linalg.norm(b-c),abs(den)/np.linalg.norm(c-a),abs(den)/np.linalg.norm(a-b)])
                flags=[True]*3 if mode=='triangles' else flags
                edge=np.full(wa.shape,False)
                for weight,height,show in zip((wa,wb,wc),alt,flags):
                    if show:edge|=weight*height<.9
                patch[visible&edge]=col*.57
            old[visible]=depth[visible]
    return Image.fromarray(np.uint8(rgb)),zbuffer


def image(mode):
    im,depth=raster(mode)
    if mode in ('quads','triangles'):return im
    if mode=='points':
        samples=gaussians(spacing=.12);points=project(samples.centers)
        im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
        for i in np.argsort(samples.centers@EYE):
            x,y=points[i];ix,iy=round(x),round(y)
            if not(0<=ix<W and 0<=iy<H) or samples.normals[i]@EYE<=0:continue
            if samples.centers[i]@EYE<depth[iy,ix]-.035:continue
            color=tuple(np.uint8(samples.colors[i]*255))
            d.ellipse((x-3,y-3,x+3,y+3),fill=color)
        return im
    if mode=='gaussians':
        from animate_gaussian_cabinet import CENTERS,COVS,COLORS
        matrix=SCALE*np.array([RIGHT,-UP]);cov=matrix@COVS@matrix.T
        return blend_splats(project(CENTERS),cov,COLORS,-CENTERS@EYE,W,H,.94).convert('RGB')
    # Diagnostic field queries are overlays on a faint, complete cabinet.
    im=Image.blend(Image.new('RGB',(W,H),PAPER),im,.27);d=ImageDraw.Draw(im)
    samples=np.array([[0,-.49,.64],[0,-.49,-.4],[.62,0,.2]])
    sigma,colors=field(samples)
    assert np.all(sigma>30)
    for point,col in zip(samples,colors):
        x,y=project(point);d.ellipse((x-11,y-11,x+11,y+11),fill=tuple(np.uint8(col*255)),outline='white',width=3)
    d.rounded_rectangle((45,572,635,626),radius=4,fill='#f8f7f3',outline='#e8e5de',width=2)
    d.text((340,599),'Query a position → color + density',font=font(26),fill='#313a37',anchor='mm')
    return im


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    for mode in ('points','quads','triangles','gaussians','field'):
        image(mode).save(OUT/f'cabinet-representation-{mode}.png')
    print('Five shared-cabinet representations rendered with visible-surface depth tests.')


if __name__=='__main__':main()
