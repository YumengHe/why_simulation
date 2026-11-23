#!/usr/bin/env python3
"""Drawer components and origin diagrams from the shared scripted cabinet.

All sizes and poses come from shared_cabinet.py. The origin illustration
intentionally shows the body faintly so the internal drawer and both origins
can be inspected. PNG assets are depth-tested; no hand-drawn cabinet replaces
this geometry. Also creates small transparent cabinet views used by frames.js.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from shared_cabinet import mesh, CabinetMesh, PART_BY_NAME
from preview_shared_cabinet import render, font

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'book/assets/diagrams'
MODEL_OUT=ROOT/'book/assets/cabinet-model'
ORANGE=(224,137,65)
PAPER=(254,253,251)
J=np.array([0.,-.46,.53]);O=np.zeros(3)
EYE=np.array([3.,-6.,3.2]);EYE/=np.linalg.norm(EYE)
RIGHT=np.cross([0.,0.,1.],EYE);RIGHT/=np.linalg.norm(RIGHT);UP=np.cross(EYE,RIGHT)


def select(model,mask):
    return CabinetMesh(model.triangles[mask],model.colors[mask].copy(),model.groups[mask],model.names[mask])


def drawer():
    m=mesh(groups={'drawer'})
    m.colors[m.names=='drawer-right-wall']=ORANGE
    return m


def arrow(d,a,b,color,width=5):
    a,b=np.array(a),np.array(b);v=(b-a)/np.linalg.norm(b-a);p=np.array([-v[1],v[0]])
    d.line([tuple(a),tuple(b-v*10)],fill=color,width=width)
    d.polygon([tuple(b),tuple(b-v*18+p*7),tuple(b-v*18-p*7)],fill=color)


def origins():
    size=(860,860);scale=300.;xy=np.array([445.,440.]);center=np.zeros(3)
    model=mesh();context=select(model,model.groups!='drawer')
    im=render(context,size,EYE,center,scale,ss=2,xy=xy)
    im=Image.blend(Image.new('RGB',size,PAPER),im,.23)
    tray=render(drawer(),size,EYE,center,scale,ss=2,xy=xy,transparent=True)
    im.paste(tray,(0,0),tray)
    d=ImageDraw.Draw(im)
    def project(p):return xy+scale*np.array([np.dot(p,RIGHT),-np.dot(p,UP)])
    a,b=project(O),project(J);v=(b-a)/np.linalg.norm(b-a);normal=np.array([-v[1],v[0]])
    arrow(d,a+normal*12,b+normal*12,'#3d739d')
    arrow(d,b-normal*12,a-normal*12,'#ad8126')
    for point,name,color,offset in ((a,'O','#313a37',(35,18)),(b,'J','#3d739d',(-38,-31))):
        x,y=point;d.ellipse((x-9,y-9,x+9,y+9),fill=color,outline='white',width=3)
        d.text(tuple(point+offset),name,font=font(40,True),fill=color,anchor='mm',stroke_width=3,stroke_fill=PAPER)
    mid=(a+b)/2
    for pos,label,color in ((mid+normal*77,'O → J','#3d739d'),(mid-normal*83,'J → O','#ad8126')):
        x,y=pos
        d.rounded_rectangle((x-62,y-24,x+62,y+24),radius=5,fill=PAPER,outline='#e4e0d7',width=1)
        d.text((x,y),label,font=font(29,True),fill=color,anchor='mm')
    d.text((430,51),'The drawer in its closed position',font=font(31,True),fill='#313a37',anchor='mm')
    d.text((430,782),'Body shown faintly to reveal the drawer.',font=font(28),fill='#656158',anchor='mm')
    d.text((430,824),'Orange: one drawer side panel',font=font(27),fill='#656158',anchor='mm')
    return im


def main():
    OUT.mkdir(exist_ok=True,parents=True);MODEL_OUT.mkdir(exist_ok=True,parents=True)
    m=drawer();panel=select(m,m.names=='drawer-right-wall')
    render(m,(640,440),eye=(3,-6,5),center=(0,-.12,.53),scale=400,ss=2).save(OUT/'drawer-shapes.png')
    eye=np.array([6.,-3.,2.6]);eye/=np.linalg.norm(eye)
    center=(np.array(PART_BY_NAME['drawer-right-wall']['lo'])+np.array(PART_BY_NAME['drawer-right-wall']['hi']))/2
    render(panel,(640,440),eye=eye,center=center,scale=590,ss=2).save(OUT/'side-panel-shape.png')
    im=render(panel,(640,440),eye=eye,center=center,scale=590,ss=2,edges=True)
    # Only front-facing vertices are marked; rear corners remain occluded.
    d=ImageDraw.Draw(im);right=np.cross([0,0,1],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
    visible=[]
    for tri in panel.triangles:
        normal=np.cross(tri[1]-tri[0],tri[2]-tri[0])
        if normal@eye>0:visible.extend(tri)
    for p in np.unique(np.round(visible,9),axis=0):
        x,y=np.array([320,220])+590*np.array([(p-center)@right,-(p-center)@up])
        d.ellipse((x-5,y-5,x+5,y+5),fill='#804523',outline='white',width=2)
    im.save(OUT/'side-panel-mesh.png')
    origins().save(OUT/'cabinet-origins.png')
    for name,q in [('closed',0.),('drawer-open',.22)]:
        render(mesh(drawer=q),(240,376),eye=(3,-6,2.6),center=(0,-.1,0),scale=155,ss=2,transparent=True).save(MODEL_OUT/f'frame-{name}.png')
    print('Shared cabinet frame diagrams and transparent miniature views rendered.')


if __name__=='__main__':main()
