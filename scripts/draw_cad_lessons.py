#!/usr/bin/env python3
"""Reproducible CAD lesson diagrams, using the canonical cabinet handle.

Analytic illustrations only: no CAD kernel, research model, or robot test is run.
"""
from pathlib import Path
from io import BytesIO
from base64 import b64encode, b64decode
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from preview_shared_cabinet import font
from html import escape
import json, math
import numpy as np
from draw_cad_examples import handle, R, L
OUT=Path(__file__).resolve().parents[1]/'book/assets/cad-lessons'
INK='#292b29'; MUTED='#69675f'; GOLD='#a87a20'; BLUE='#4e83a7'; TEAL='#528682'; LINE='#dddcd4'; PAPER='#fefdfb'
def text(x,y,s,size=21,color=INK,anchor='start',bold=False):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{600 if bold else 400}">{escape(s)}</text>'
def path(points,color=GOLD,dash=False,width=2):
    return '<polyline points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="6 5"' if dash else '')+'/>'
def arrow(a,b,color=GOLD):
    v=np.array(b)-a; v=v/np.linalg.norm(v); side=np.array([-v[1],v[0]])
    return path([a,b],color)+path([np.array(b)-10*v+4*side,b,np.array(b)-10*v-4*side],color)
def rect(x,y,w,h,fill='#f7f5ef',stroke=LINE):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}"/>'
def circle(x,y,r,fill='none',stroke=BLUE):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
def image(im,x,y,w,h):
    buf=BytesIO();im.save(buf,format='PNG')
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{b64encode(buf.getvalue()).decode()}"/>'
def save(name,title,body,height=430):
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="{height}" viewBox="0 0 600 {height}" role="img"><title>{escape(title)}</title><rect width="600" height="{height}" fill="{PAPER}"/><g font-family="Arial, sans-serif">'+body+'</g></svg>'
    if '<image ' in s:
        rasterize(s, OUT/(name+'.png'))
        (OUT/(name+'.svg')).unlink(missing_ok=True)
    else:
        (OUT/(name+'.svg')).write_text(s)

def rasterize(svg, destination):
    """Draw our limited SVG vocabulary with Pillow, retaining scripted raster inputs.

    The published PNG has a single auditable generator; published SVGs stay vector-only.
    """
    root=ET.fromstring(svg);ss=2
    canvas=Image.new('RGB',(600*ss,int(root.attrib['height'])*ss),PAPER);d=ImageDraw.Draw(canvas)
    def col(a,k,default=None):
        value=a.get(k,default);return None if value=='none' else value
    for el in root.iter():
        tag=el.tag.rsplit('}',1)[-1];a=el.attrib
        def val(k,default=0):return float(a.get(k,default))*ss
        width=max(1,round(val('stroke-width',1)))
        if tag=='rect':
            d.rounded_rectangle((val('x'),val('y'),val('x')+val('width'),val('y')+val('height')),radius=val('rx'),fill=col(a,'fill'),outline=col(a,'stroke'),width=width)
        elif tag in ('circle','ellipse'):
            rx=val('r') if tag=='circle' else val('rx');ry=val('r') if tag=='circle' else val('ry')
            d.ellipse((val('cx')-rx,val('cy')-ry,val('cx')+rx,val('cy')+ry),fill=col(a,'fill'),outline=col(a,'stroke'),width=width)
        elif tag in ('polyline','polygon'):
            pts=[tuple(float(x)*ss for x in pair.split(',')) for pair in a['points'].split()]
            if tag=='polygon':d.polygon(pts,fill=col(a,'fill'));pts+=[pts[0]]
            d.line(pts,fill=col(a,'stroke',INK),width=width,joint='curve')
        elif tag=='text':
            anchor={'middle':'ms','end':'rs'}.get(a.get('text-anchor'),'ls')
            d.text((val('x'),val('y')),el.text or '',font=font(round(val('font-size',21)),a.get('font-weight')=='600'),fill=col(a,'fill',INK),anchor=anchor)
        elif tag=='image':
            im=Image.open(BytesIO(b64decode(a['href'].split(',',1)[1]))).convert('RGB')
            box=(round(val('width')),round(val('height')));im.thumbnail(box,Image.Resampling.LANCZOS)
            canvas.paste(im,(round(val('x'))+(box[0]-im.width)//2,round(val('y'))+(box[1]-im.height)//2))
    canvas.save(destination,optimize=True)

def heading(kicker,title):
    return text(24,31,kicker.upper(),15,GOLD)+text(24,69,title,27,bold=True)
def dimension(a,b,label,at):
    v=np.array(b)-a;v=v/np.linalg.norm(v);side=np.array([-v[1],v[0]])*6
    return path([a,b],BLUE)+path([np.array(a)-side,np.array(a)+side],BLUE)+path([np.array(b)-side,np.array(b)+side],BLUE)+text(*at,label,20,BLUE,anchor='middle')
def front_handle(x=80,y=170,scale=.88):
    # Orthographic front silhouette: grip length 500, diameter 100; supports x=+-210.
    w=500*scale;h=100*scale
    s=rect(x,y,w,h,'#d8e2e2',TEAL)
    for u in (40,460):s+=rect(x+(u-36)*scale,y+22*scale,72*scale,56*scale,'#becfce',TEAL)
    return s

def representations():
    """One consistent 3D drawing style, with labels outside the geometry."""
    from types import SimpleNamespace
    from shared_cabinet import PART_BY_NAME, part_triangles
    from preview_shared_cabinet import render
    scale=2
    im=Image.new('RGB',(1200,1540),PAPER);d=ImageDraw.Draw(im)
    def t(x,y,value,size=20,color=INK,bold=False,anchor='ls'):
        d.text((x*scale,y*scale),value,font=font(size*scale,bold),fill=color,anchor=anchor)
    def rule(y):d.line((24*scale,y*scale,576*scale,y*scale),fill=LINE,width=2)
    def model(mode,w,h):
        parts=[dict(v) for k,v in PART_BY_NAME.items() if k.startswith('drawer-handle')]
        if mode in ('grip','brep'):parts=parts[:1]
        triangles=[];colors=[]
        for part in parts:
            tri=part_triangles(part,64)
            col=np.tile([138.,179.,176.],(len(tri),1))
            if mode=='brep':
                col[np.arange(len(tri))%4>=2]=[217.,173.,89.]
            if mode=='separate' and part['name']!='drawer-handle-grip':
                tri=tri+[0,.10,.16]
                col[:]=[217.,173.,89.]
            triangles.extend(tri);colors.extend(col)
        tri=np.array(triangles); center=(tri.min(axis=(0,1))+tri.max(axis=(0,1)))/2
        eye=np.array([3.,-6.,2.6]);eye/=np.linalg.norm(eye)
        right=np.cross([0,0,1],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
        xy=np.stack([(tri-center)@right,-(tri-center)@up],axis=-1).reshape(-1,2)
        lo,hi=xy.min(0),xy.max(0);factor=min((w*2-40)/(hi[0]-lo[0]),(h*2-30)/(hi[1]-lo[1]))
        origin=np.array([w,h])-factor*(lo+hi)/2
        return render(SimpleNamespace(triangles=tri,colors=np.array(colors)),size=(w*2,h*2),center=center,scale=factor,ss=2,xy=origin)
    def put(mode,x,y,w,h):im.paste(model(mode,w,h),(x*2,y*2))
    def arr(x,y):
        d.line((x*2,y*2,(x+24)*2,y*2),fill=GOLD,width=3)
        d.line(((x+17)*2,(y-5)*2,(x+24)*2,y*2,(x+17)*2,(y+5)*2),fill=GOLD,width=3)
    t(24,33,'01   BOUNDARY REPRESENTATION',14,GOLD)
    t(24,68,'Describe the enclosing surfaces',25,bold=True)
    put('brep',75,84,450,160)
    t(300,255,'Curved side  +  flat end faces',19,MUTED,anchor='ms')
    rule(280)
    t(24,312,'02   CONSTRUCTIVE SOLID GEOMETRY',14,GOLD)
    t(24,347,'Combine three solid cylinders',25,bold=True)
    put('separate',26,365,240,140);put('whole',334,365,240,140);arr(288,432)
    t(146,526,'Separate solids',18,MUTED,anchor='ms');t(454,526,'Union',18,MUTED,anchor='ms')
    rule(550)
    t(24,582,'03   PARAMETRIC HISTORY',14,GOLD)
    t(24,617,'Keep the steps and dimensions',25,bold=True)
    # Project a circle on the same grip end plane and camera as the rendered cylinder.
    eye=np.array([3.,-6.,2.6]);eye/=np.linalg.norm(eye)
    right=np.cross([0,0,1],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
    points=[]
    for u in np.linspace(0,2*np.pi,129):
        v=np.array([0,math.cos(u),math.sin(u)])
        points.append(((91+38*v@right)*2,(680-38*v@up)*2))
    d.polygon(points,fill='#e5eeec');d.line(points,fill=TEAL,width=3)
    put('grip',207,640,150,85);put('whole',419,640,150,85);arr(163,680);arr(371,680)
    t(91,748,'Sketch a circle',16,MUTED,anchor='ms');t(282,748,'Extrude to length',16,MUTED,anchor='ms');t(494,748,'Add supports',16,MUTED,anchor='ms')
    im.save(OUT/'representations.png',optimize=True)

def applications():
    b=heading('01 · Replacement handle','Specify the dimensions')+front_handle()
    b+=dimension((80,131),(520,131),'Grip length: 500 mm',(300,117))
    for x in (115.2,484.8):b+=path([(x,203),(x,336)],MUTED,True)
    b+=dimension((115.2,322),(484.8,322),'Support centers: 420 mm',(300,355))
    b+=text(300,397,'Grip radius: 50 mm · front view',20,MUTED,'middle')
    save('replacement','Dimensioned front view of the shared handle',b)
    # End-on view through the grip center; support locations are outside the slice.
    b=heading('02 · Clearance','Measure the empty space')
    b+=rect(403,110,85,230,'#6998b6',BLUE)+circle(195,225,65,'#d8e2e2',TEAL)
    b+=path([(195,160),(195,100)],MUTED,True)+text(195,95,'Grip cross-section',18,anchor='middle')
    b+=dimension((260,225),(403,225),'110 mm gap',(331.5,204))
    b+=text(445,368,'Drawer front',18,BLUE,'middle')+text(195,325,'r = 50 mm',20,TEAL,'middle')
    b+=text(300,405,'Slice through the middle, between the supports.',18,MUTED,'middle')
    # Drawing is schematic; numeric gap comes from canonical part coordinates.
    from shared_cabinet import PART_BY_NAME
    front_y=PART_BY_NAME['drawer-front-center']['lo'][1]
    grip_y=PART_BY_NAME['drawer-handle-grip']['start'][1]
    gap=front_y-(grip_y+R);assert math.isclose(gap,.11)
    spacing=PART_BY_NAME['drawer-handle-right-support']['start'][0]-PART_BY_NAME['drawer-handle-left-support']['start'][0]
    assert math.isclose(spacing,.42) and math.isclose(L,.5)
    save('clearance','Gap between the grip and the drawer front',b)
    b=heading('03 · Surface analysis','Ask which way the surface faces')
    c=np.array([200.,230.]);n=np.array([.6,-.8]);p=c+90*n;t=np.array([.8,.6])
    assert abs(n@t)<1e-12
    b+=circle(*c,90,'#e2ecea',TEAL)+path([c,p],TEAL,True)+arrow(p,p+95*n,BLUE)+arrow(p-75*t,p+95*t,GOLD)+circle(*p,5,GOLD,GOLD)
    b+=text(340,127,'Normal',21,BLUE)+text(340,155,'Points outward',17,MUTED)
    b+=text(347,225,'Tangent',21,GOLD)+text(347,253,'Runs along the surface',17,MUTED)
    b+=text(300,370,'Around the grip: curvature = 1 / radius',20,anchor='middle')+text(300,402,'Along its straight axis: curvature = 0',18,MUTED,'middle')
    save('surface-analysis','Tangent, normal, and curvature on the cylindrical grip',b)
    b=heading('04 · Experiment variants','Change one design parameter')
    for y,r in [(78,.035),(225,.05),(372,.065)]:
        b+=image(handle(r=r),20,y,340,150)+text(400,y+70,f'r = {int(r*1000)} mm',24,bold=True)
    b+=text(300,541,'Same length, axis, and support dimensions.',20,MUTED,'middle')
    b+=text(300,575,'Export each variant for a separate robot test.',18,MUTED,'middle')
    save('variants','Three grip radii with the same handle construction',b,600)

def pointcloud():
    # Sample the three canonical cylinder sides, project with the handle-view camera.
    from shared_cabinet import PART_BY_NAME
    from PIL import Image,ImageDraw
    im=Image.new('RGB',(340,150),PAPER);d=ImageDraw.Draw(im)
    eye=np.array([3.,-6.,2.6]);eye/=np.linalg.norm(eye);right=np.cross([0,0,1],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
    rng=np.random.default_rng(23)
    for name,p in PART_BY_NAME.items():
        if not name.startswith('drawer-handle'):continue
        a=np.array(p['start']);v=np.array(p['end'])-a;axis=v/np.linalg.norm(v)
        q=np.array([0.,0.,1.]);e=np.cross(axis,q);e/=np.linalg.norm(e);f=np.cross(axis,e)
        for u,t in rng.uniform(0,1,(450,2)):
            xyz=a+t*v+p['radius']*(np.cos(2*np.pi*u)*e+np.sin(2*np.pi*u)*f)-[0,-.57,.53]
            x,y=170+525*xyz@right,75-525*xyz@up;d.ellipse((x-1.1,y-1.1,x+1.1,y+1.1),fill=TEAL)
    return im

def research(name,kicker,title,input_title,input_lines,step_title,step_lines,output_title,output_lines,kind):
    b=heading(kicker,title)
    for y,idx,ttl,lines in [(94,'01',input_title,input_lines),(260,'02',step_title,step_lines),(426,'03',output_title,output_lines)]:
        b+=rect(20,y,560,140)+text(36,y+27,idx,16,GOLD)+text(75,y+29,ttl,23,bold=True)
        for j,s in enumerate(lines):b+=text(232,y+66+26*j,s,18,MUTED)
        if y<426:b+=arrow((300,y+143),(300,y+163),MUTED)
    if kind=='text':
        b+=text(42,155,'A round grip',18,TEAL)+text(42,181,'with two',18,TEAL)+text(42,207,'supports',18,TEAL)
    else:b+=image(pointcloud() if kind=='points' else handle(),29,137,190,84)
    if kind=='image':
        b+=text(45,330,'Parts → numbers',18,TEAL)+text(45,360,'r, L, positions',18,TEAL)
    elif kind=='constraint':
        b+=text(45,330,'Shape',20,TEAL)+text(45,360,'+ relationships',18,GOLD)
    else:
        b+=circle(65,340,20,'#e3eeee',TEAL)+arrow((92,340),(125,340))+rect(137,320,70,40,'#d7e5e4',TEAL)
    b+=image(handle(),29,468,190,84)
    b+=text(300,600,'Scripted explanation using our handle, not a model prediction.',16,MUTED,'middle')
    save(name,title,b,625)

def main():
    OUT.mkdir(parents=True,exist_ok=True);representations();applications()
    research('text2cad','Text2CAD · NeurIPS 2024','From words to construction steps','Text description',['Describe a part and,','optionally, its dimensions.'],'Predict a CAD sequence',['Learned model proposes','sketch and extrusion steps.'],'Execute the sequence',['Build the proposed part.','Inspect and edit the design.'],'text')
    research('cad-recode','CAD-Recode · ICCV 2025','From sampled points to CAD code','Point cloud',['3D samples on a part.','They provide shape evidence.'],'Predict Python code',['The model writes a','CadQuery construction program.'],'Run the CAD program',['Construct the solid from code.','Keep the program for editing.'],'points')
    research('img2cad','Img2CAD · SIGGRAPH Asia 2025','From an image to an editable part','One image',['Pixels show the visible','shape and arrangement.'],'Predict structure, then numbers',['A VLM proposes the parts','and commands; TrAssembler','predicts numerical values.'],'Execute the CAD program',['Build the proposed geometry.','Inspect its parts and dimensions.'],'image')
    b=heading('ConCAD · September 2026 preprint','Learn shape and design relationships')
    for y,idx,title,lines in [(94,'01','One rendered part image',['Visual evidence about the part.']), (228,'02','Generate a CAD program',['The trained model predicts','executable CadQuery code.']), (362,'03','Run and inspect the program',['Build the proposed solid.','Check its shape and relations.'])]:
        b+=rect(20,y,560,110)+text(36,y+27,idx,16,GOLD)+text(75,y+29,title,23,bold=True)
        for j,line_ in enumerate(lines): b+=text(232,y+64+24*j,line_,18,MUTED)
        if y!=228:b+=image(handle(),30,y+33,163,72)
        else:b+=text(42,y+68,'CAD instructions',18,TEAL)
        if y<362:b+=arrow((300,y+113),(300,y+131),MUTED)
    b+=rect(20,497,560,83,'#faf6e9')+text(36,523,'During training',18,GOLD,bold=True)
    b+=text(36,548,'Feedback uses code relationships and executed shape.',18)+text(36,570,'Reference programs and solids supply the targets.',17,MUTED)
    b+=text(300,609,'Scripted teaching example, not a model prediction.',16,MUTED,'middle')
    save('concad','ConCAD generation with separate training feedback',b,625)
    (OUT/'manifest.json').write_text(json.dumps({'generator':'scripts/draw_cad_lessons.py','source_geometry':'scripts/shared_cabinet.py','units':'millimeters in diagram labels','grip_radius_mm':50,'grip_length_mm':500,'support_center_spacing_mm':420,'center_slice_clearance_mm':110,'variant_radii_mm':[35,50,65],'research_illustrations':'Authored workflow examples, not model outputs. No named model, CAD kernel, or robot simulation was run.','works':{'Text2CAD':'https://sadilkhan.github.io/text2cad-project/','CAD-Recode':'https://github.com/filaPro/cad-recode','Img2CAD':'https://qq456cvb.github.io/projects/img2cad','ConCAD':'https://arxiv.org/abs/2609.34494'}},indent=2)+'\n')
    print('Generated nine lesson diagrams. Verified clearance and tangent-normal orthogonality.')
if __name__=='__main__':main()
