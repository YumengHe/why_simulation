"""Opaque per-pixel visibility for the legacy-frame URDF demonstrations."""
import numpy as np
from PIL import Image

def layer(data,pose,project,links,size,aa=2):
    w,h=size;w*=aa;h*=aa
    pixels=np.zeros((h,w,4),np.uint8);depths=np.full((h,w),-np.inf)
    light=np.array([-3.,7.,5.]);light/=np.linalg.norm(light)
    for m in data['meshes']:
        if m['link'] not in links:continue
        vs=pose(m)
        if vs is None:continue
        for tri in vs[np.array(m['faces'])]:
            n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=np.linalg.norm(n)
            if n@project.eye<=1e-9:continue
            xy=np.array([project(v) for v in tri])*aa;z=tri@project.eye
            x0,y0=np.maximum(np.floor(xy.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(xy.max(0)).astype(int)+1,[w,h])
            if x0>=x1 or y0>=y1:continue
            a,b,c=xy;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-10:continue
            yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
            wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;wc=1-wa-wb
            depth=wa*z[0]+wb*z[1]+wc*z[2];old=depths[y0:y1,x0:x1]
            visible=(wa>=0)&(wb>=0)&(wc>=0)&(depth>old)
            col=np.array(m['color'])*(.65+.35*max(0,n@light))
            pixels[y0:y1,x0:x1][visible]=list(col.astype(np.uint8))+[255];old[visible]=depth[visible]
    return Image.fromarray(pixels)
