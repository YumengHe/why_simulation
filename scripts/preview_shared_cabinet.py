#!/usr/bin/env python3
"""Render and export the canonical cabinet with opaque, depth-tested faces.

Run with the book's Python environment. The output geometry and pictures are
entirely script-produced. This is an authored teaching asset, not a generated
image or a reconstruction result.
"""
from pathlib import Path
import json
import math
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shared_cabinet import mesh, validate, PARTS, BOX_PARTS, CYLINDER_PARTS, DRAWER_LIMIT, DOOR_LIMIT, HINGE, part_triangles

OUT=Path(__file__).resolve().parents[1]/'book/assets/cabinet-model'
PAPER=(254,253,251)
INK=(42,48,48)
MUTED=(100,108,105)
LIGHT=np.array([-3.,-5.,7.]); LIGHT/=np.linalg.norm(LIGHT)


def font(size,bold=False):
    names=['Arial Bold.ttf','Arial.ttf'] if bold else ['Arial.ttf']
    for name in names:
        path=Path('/System/Library/Fonts/Supplemental')/name
        if path.exists(): return ImageFont.truetype(str(path),size)
    return ImageFont.load_default(size=size)


def render(model, size=(600,650), eye=(3.,-6.,2.6), center=(0.,-.2,0.), scale=255., ss=2, edges=False, xy=None, transparent=False):
    """Orthographic opaque rasterization; returns an RGB PIL image.

    ``eye`` points from the object to the observer. ``center`` is the framing
    point. A z-buffer resolves visibility, including all backfaces/occlusion.
    Optional triangle outlines are depth-tested, not drawn through surfaces.
    """
    w,h=size; W,H=w*ss,h*ss
    screen_center=np.array([w/2,h/2] if xy is None else xy)
    eye=np.asarray(eye,float); eye/=np.linalg.norm(eye)
    right=np.cross(np.array([0.,0.,1.]),eye); right/=np.linalg.norm(right)
    up=np.cross(eye,right)
    rgb=np.full((H,W,3),PAPER,dtype=float)
    depth=np.full((H,W),-np.inf)
    for tri,color in zip(model.triangles,model.colors):
        normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]); normal/=np.linalg.norm(normal)
        if normal@eye<=1e-10: continue
        p=tri-np.asarray(center)
        pts=np.column_stack((screen_center[0]+scale*(p@right),screen_center[1]-scale*(p@up)))*ss
        zz=tri@eye
        x0,y0=np.maximum(np.floor(pts.min(axis=0)).astype(int),0)
        x1,y1=np.minimum(np.ceil(pts.max(axis=0)).astype(int)+1,[W,H])
        if x1<=x0 or y1<=y0: continue
        yy,xx=np.mgrid[y0:y1,x0:x1]; xx=xx+.5; yy=yy+.5
        a,b,c=pts
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-12: continue
        wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
        wc=1-wa-wb
        z=wa*zz[0]+wb*zz[1]+wc*zz[2]
        old=depth[y0:y1,x0:x1]
        visible=(wa>=-1e-9)&(wb>=-1e-9)&(wc>=-1e-9)&(z>old)
        shade=.65+.35*max(0,normal@LIGHT)
        patch=rgb[y0:y1,x0:x1]
        patch[visible]=np.asarray(color)*shade
        if edges:
            altitudes=np.array([abs(den)/np.linalg.norm(b-c),abs(den)/np.linalg.norm(c-a),abs(den)/np.linalg.norm(a-b)])
            border=np.minimum.reduce([wa*altitudes[0],wb*altitudes[1],wc*altitudes[2]])<.45*ss
            patch[visible&border]*=.72
        old[visible]=z[visible]
    pixels=np.uint8(np.clip(rgb,0,255))
    if transparent:
        pixels=np.dstack((pixels,np.uint8(np.isfinite(depth))*255))
    return Image.fromarray(pixels).resize((w,h),Image.Resampling.LANCZOS)


def export_obj(n=32):
    model=mesh(n)
    lines=['# Canonical teaching cabinet; authored by scripts/shared_cabinet.py',
           '# X right, -Y front, Z up; metres. Two independent joints.',
           'mtllib cabinet.mtl']
    materials=[]
    offset=1
    for part in PARTS:
        tris=model.triangles[model.names==part['name']]
        lines.extend([f'o {part["name"]}',f'g {part["group"]}',f'usemtl {part["name"]}'])
        # Deduplicate vertices per closed primitive for an inspectable mesh.
        vertices={}; faces=[]
        for tri in tris:
            face=[]
            for point in tri:
                key=tuple(np.round(point,10))
                if key not in vertices: vertices[key]=offset+len(vertices)
                face.append(vertices[key])
            faces.append(face)
        lines.extend('v '+' '.join(f'{v:.8f}' for v in p) for p in vertices)
        lines.extend('f '+' '.join(map(str,face)) for face in faces)
        offset+=len(vertices)
        color=np.asarray(part['color'])/255.
        materials.extend([f'newmtl {part["name"]}', 'Kd '+' '.join(f'{v:.6f}' for v in color),'d 1.0','illum 1',''])
    (OUT/'cabinet.obj').write_text('\n'.join(lines)+'\n')
    (OUT/'cabinet.mtl').write_text('\n'.join(materials).rstrip()+'\n')


def export_urdf(n=32):
    """A two-joint kinematic URDF plus named local component meshes.

    Body and drawer coordinates equal the closed cabinet frame; door meshes
    are translated to the hinge frame. Each primitive also supplies a simple
    collision element. Mass/inertia are intentionally not assigned here.
    """
    meshes=OUT/'meshes'; meshes.mkdir(exist_ok=True)
    robot=ET.Element('robot',name='teaching_cabinet')
    robot.append(ET.Comment('Authored teaching model: fixed handles; drawer slide and door hinge. Supply mass and inertia for a dynamics experiment.'))
    def vec(values):return ' '.join(f'{float(v):.8g}' for v in values)
    for group in ('body','drawer','door'):
        link=ET.SubElement(robot,'link',name=group)
        offset=HINGE if group=='door' else np.zeros(3)
        for part in PARTS:
            if part['group']!=group:continue
            tris=part_triangles(part,n)-offset
            verts={};faces=[]
            for tri in tris:
                face=[]
                for point in tri:
                    key=tuple(np.round(point,10))
                    if key not in verts:verts[key]=len(verts)+1
                    face.append(verts[key])
                faces.append(face)
            lines=[f'# {part["name"]}; coordinates in {group} link frame']
            lines+=['v '+vec(p) for p in verts]
            lines+=['f '+' '.join(map(str,face)) for face in faces]
            filename=f'meshes/{part["name"]}.obj'
            (OUT/filename).write_text('\n'.join(lines)+'\n')
            visual=ET.SubElement(link,'visual',name=part['name'])
            geometry=ET.SubElement(visual,'geometry')
            ET.SubElement(geometry,'mesh',filename=filename)
            material=ET.SubElement(visual,'material',name=part['name']+'-material')
            ET.SubElement(material,'color',rgba=vec(list(np.asarray(part['color'])/255.)+[1]))
            collision=ET.SubElement(link,'collision',name=part['name']+'-contact')
            if part['kind']=='box':
                lo,hi=np.asarray(part['lo']),np.asarray(part['hi'])
                ET.SubElement(collision,'origin',xyz=vec((lo+hi)/2-offset),rpy='0 0 0')
                geometry=ET.SubElement(collision,'geometry')
                ET.SubElement(geometry,'box',size=vec(hi-lo))
            else:
                start,end=np.asarray(part['start']),np.asarray(part['end'])
                axis=end-start;length=np.linalg.norm(axis);axis/=length
                rpy=[0,math.acos(np.clip(axis[2],-1,1)),math.atan2(axis[1],axis[0])]
                ET.SubElement(collision,'origin',xyz=vec((start+end)/2-offset),rpy=vec(rpy))
                geometry=ET.SubElement(collision,'geometry')
                ET.SubElement(geometry,'cylinder',radius=str(part['radius']),length=f'{length:.8g}')
    joint=ET.SubElement(robot,'joint',name='drawer_slide',type='prismatic')
    ET.SubElement(joint,'parent',link='body');ET.SubElement(joint,'child',link='drawer')
    ET.SubElement(joint,'origin',xyz='0 0 0',rpy='0 0 0');ET.SubElement(joint,'axis',xyz='0 -1 0')
    ET.SubElement(joint,'limit',lower='0',upper=str(DRAWER_LIMIT),effort='100',velocity='1')
    joint=ET.SubElement(robot,'joint',name='door_hinge',type='revolute')
    ET.SubElement(joint,'parent',link='body');ET.SubElement(joint,'child',link='door')
    ET.SubElement(joint,'origin',xyz=vec(HINGE),rpy='0 0 0');ET.SubElement(joint,'axis',xyz='0 0 -1')
    ET.SubElement(joint,'limit',lower='0',upper=f'{math.radians(DOOR_LIMIT):.9f}',effort='20',velocity='2')
    ET.indent(robot,space='  ')
    ET.ElementTree(robot).write(OUT/'cabinet.urdf',encoding='utf-8',xml_declaration=True)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    counts=[validate(n) for n in (6,32)]
    views=[
        ('front','Front view',mesh(),(0.,-1.,.03),(0.,0.,0.),260.),
        ('three-quarter','Closed cabinet',mesh(),(3.,-6.,2.6),(0.,-.13,0.),250.),
        ('open','Drawer and door open',mesh(drawer=.50,door=65),(-3.,-6.,3.3),(-.13,-.40,0.),225.),
    ]
    sheet=Image.new('RGB',(1800,820),PAPER)
    draw=ImageDraw.Draw(sheet)
    draw.text((45,28),'One cabinet throughout the book',font=font(38,True),fill=INK)
    draw.text((45,82),'Teal body · blue sliding drawer · gold hinged door · fixed pull handles',font=font(23),fill=MUTED)
    for i,(name,title,model,eye,center,scale) in enumerate(views):
        im=render(model,(560,600),eye,center,scale,ss=3)
        im.save(OUT/f'{name}.png')
        sheet.paste(im,(20+i*600,168))
        draw.text((300+i*600,145),title,font=font(26,True),fill=INK,anchor='mm')
        if i>0: draw.line((i*600,135,i*600,765),fill=(222,221,216),width=2)
    draw.text((45,786),'2 degrees of freedom: drawer slide + door rotation. Both handles move with their panels.',font=font(22),fill=MUTED)
    sheet.save(OUT/'preview.png')
    export_obj()
    export_urdf()
    closed=mesh()
    (OUT/'geometry.json').write_text(json.dumps({
        'source':'scripts/shared_cabinet.py','coordinates':'X right; -Y front; Z up; metres',
        'triangles':closed.triangles.round(8).tolist(),'colors':closed.colors.tolist(),
        'groups':closed.groups.tolist(),'names':closed.names.tolist(),
        'drawer_axis':[0,-1,0],'drawer_limit':DRAWER_LIMIT,
        'door_hinge':HINGE.tolist(),'door_axis':[0,0,-1],'door_limit_degrees':DOOR_LIMIT,
    },separators=(',',':'))+'\n')
    (OUT/'model.json').write_text(json.dumps({
        'source':'scripts/shared_cabinet.py','units':'metres',
        'axes':{'x':'right','y':'back','z':'up'},
        'body_dimensions':{'width':1.24,'depth':.86,'height':1.72},
        'joints':[{'name':'drawer_slide','type':'prismatic','group':'drawer','axis':[0,-1,0], 'range':[0,DRAWER_LIMIT]},
                  {'name':'door_hinge','type':'revolute','group':'door','axis':[0,0,-1], 'origin':[-.51,-.46,0], 'range_degrees':[0,DOOR_LIMIT]}],
        'validation':counts,'parts':PARTS,
        'description':'Authored teaching cabinet. All primitive surfaces are closed and outward-wound. The front consists of five flush blue pieces; its handles are fixed to the panels. The cavity is intentionally visible only with the door or drawer open.',
    },indent=2)+'\n')
    print(f'Wrote {OUT}/preview.png and closed-pose OBJ/MTL; {counts}')


if __name__=='__main__':main()
