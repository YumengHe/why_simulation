#!/usr/bin/env python3
"""Render original low/high-detail cabinet meshes with exact triangle counts.

Seven box-shaped panels stay identical. Only the radial sampling of six capped
handle cylinders changes. Orthographic rasterization uses a depth buffer, flat
lighting and the actual triangle edges. No appearance-only smoothing is used.
"""
from pathlib import Path
import json
import math

import numpy as np
from PIL import Image, ImageDraw

from animate_projection import font

OUT = Path(__file__).resolve().parents[1] / 'book/assets/diagrams'
W, H, SS = 420, 660, 3
PAPER = (254, 253, 251)
TEAL, BLUE, GOLD = (108,153,150), (91,141,184), (219,181,85)
EYE = np.array([3.,-6.,2.])/7
RIGHT = np.array([2.,1.,0.])/math.sqrt(5)
UP = np.cross(EYE,RIGHT)
LIGHT = np.array([-2.,-4.,6.]); LIGHT /= np.linalg.norm(LIGHT)


class Mesh:
    def __init__(self):
        self.triangles=[];self.colors=[];self.groups=[]
    def triangle(self,points,color,group):
        self.triangles.append(np.array(points,float));self.colors.append(color);self.groups.append(group)
    def box(self,lo,hi,color):
        lo,hi=np.array(lo,float),np.array(hi,float)
        center=(lo+hi)/2
        vertices=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
        for indices in [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(1,5,7,3),(0,2,6,4)]:
            face=vertices[list(indices)]
            if np.cross(face[1]-face[0],face[2]-face[0]) @ (face.mean(axis=0)-center)<0:face=face[::-1]
            for tri in ((0,1,2),(0,2,3)):self.triangle(face[list(tri)],color,'panel')
    def cylinder(self,start,end,radius,n,color,group):
        start,end=np.array(start,float),np.array(end,float)
        axis=end-start;axis/=np.linalg.norm(axis)
        ref=np.array([0.,0.,1.]) if abs(axis[2])<.9 else np.array([1.,0.,0.])
        u=np.cross(axis,ref);u/=np.linalg.norm(u);v=np.cross(axis,u)
        ring=np.array([radius*(u*math.cos(2*math.pi*i/n)+v*math.sin(2*math.pi*i/n)) for i in range(n)])
        a,b=start+ring,end+ring
        for i in range(n):
            j=(i+1)%n
            for points in [(a[i],a[j],b[j]),(a[i],b[j],b[i]),(start,a[j],a[i]),(end,b[i],b[j])]:
                self.triangle(points,color,group)


def cabinet(n):
    m=Mesh()
    for lo,hi in [((-.62,-.43,-.86),(-.54,.43,.86)),((.54,-.43,-.86),(.62,.43,.86)),
                  ((-.54,.35,-.86),(.54,.43,.86)),((-.54,-.43,.79),(.54,.35,.86)),
                  ((-.54,-.43,-.86),(.54,.35,-.78))]:m.box(lo,hi,TEAL)
    m.box((-.51,-.49,.33),(.51,-.43,.74),BLUE)
    m.box((-.51,-.485,-.73),(.51,-.43,.26),GOLD)
    m.cylinder((-.25,-.65,.53),(.25,-.65,.53),.05,n,(212,219,213),'drawer-handle')
    for x in (-.21,.21):m.cylinder((x,-.49,.53),(x,-.65,.53),.036,n,(192,202,194),'drawer-handle')
    m.cylinder((.36,-.64,-.35),(.36,-.64,-.10),.045,n,(180,143,56),'door-handle')
    for z in (-.31,-.14):m.cylinder((.36,-.485,z),(.36,-.64,z),.032,n,(180,143,56),'door-handle')
    return m


def raster(mesh,groups,size,center,scale,xy):
    w,h=size;w*=SS;h*=SS
    image=np.full((h,w,3),PAPER,dtype=np.float32)
    depths=np.full((h,w),-np.inf)
    for tri,color,group in zip(mesh.triangles,mesh.colors,mesh.groups):
        if groups and group not in groups:continue
        normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal)
        if normal@EYE<=1e-9:continue
        q=tri-np.array(center)
        pts=np.column_stack([xy[0]+scale*(q@RIGHT),xy[1]-scale*(q@UP)])*SS
        z=tri@EYE
        x0,y0=np.maximum(np.floor(pts.min(axis=0)).astype(int),0)
        x1,y1=np.minimum(np.ceil(pts.max(axis=0)).astype(int)+1,[w,h])
        if x0>=x1 or y0>=y1:continue
        yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
        a,b,c=pts
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-10:continue
        wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
        wc=1-wa-wb
        depth=wa*z[0]+wb*z[1]+wc*z[2]
        old=depths[y0:y1,x0:x1]
        visible=(wa>=-1e-9)&(wb>=-1e-9)&(wc>=-1e-9)&(depth>old)
        if not visible.any():continue
        altitudes=np.array([abs(den)/np.linalg.norm(b-c),abs(den)/np.linalg.norm(c-a),abs(den)/np.linalg.norm(a-b)])
        distance=np.minimum.reduce([wa*altitudes[0],wb*altitudes[1],wc*altitudes[2]])
        edge=distance<.58*SS
        shade=.68+.32*max(0,normal@LIGHT)
        rgb=np.array(color)*shade
        patch=image[y0:y1,x0:x1]
        patch[visible]=rgb
        patch[visible&edge]=rgb*.66
        old[visible]=depth[visible]
    return Image.fromarray(np.uint8(image))


def draw(m):
    image=Image.new('RGB',(W*SS,H*SS),PAPER)
    full=raster(m,None,(W,405),(0,0,0),170,(210,205))
    image.paste(full,(0,0))
    d=ImageDraw.Draw(image)
    d.line(tuple(v*SS for v in (22,419,W-22,419)),fill='#dfdbd0',width=SS)
    d.text((W/2*SS,449*SS),'Drawer handle, enlarged',font=font(23*SS),fill='#333b3a',anchor='mm')
    detail=raster(m,{'drawer-handle'},(W,175),(0,-.57,.53),650,(210,90))
    image.paste(detail,(0,475*SS))
    # Connect the enlarged view to the exact handle on the complete cabinet.
    c=np.array([0.,-.65,.53]);xy=np.array([210+170*(c@RIGHT),205-170*(c@UP)])
    d=ImageDraw.Draw(image)
    d.rounded_rectangle(tuple(v*SS for v in (xy[0]-55,xy[1]-19,xy[0]+55,xy[1]+19)),radius=4*SS,outline='#9a7422',width=2*SS)
    return image.resize((W*2,H*2),Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    low,high=cabinet(6),cabinet(32)
    manifest=[]
    for name,n,m in [('coarse',6,low),('fine',32,high)]:
        panels=[t for t,g in zip(m.triangles,m.groups) if g=='panel']
        counts={'panels':len(panels),'handles':len(m.triangles)-len(panels),'total':len(m.triangles)}
        assert counts=={'panels':84,'handles':24*n,'total':84+24*n}
        assert all(np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))>1e-10 for t in m.triangles)
        draw(m).save(OUT/f'cabinet-mesh-{name}.png')
        manifest.append({'image':f'cabinet-mesh-{name}.png','radial_sides':n,'triangles':counts})
    assert np.array_equal(np.array(low.triangles[:84]),np.array(high.triangles[:84]))
    (OUT/'cabinet-mesh-detail.json').write_text(json.dumps({'source':'Original teaching meshes. Seven box panels and six capped handle cylinders.',
        'rendering':'Identical camera, colors, flat lighting and visible triangle edges. Depth-buffered orthographic views.',
        'views':manifest},indent=2)+'\n')
    print('Rendered cabinet meshes: 228 vs 852 triangles. The 84 panel triangles are identical.')


if __name__=='__main__':main()
