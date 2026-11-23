#!/usr/bin/env python3
"""Original cabinet cutaways for the visual-to-physics chapter.

All shapes are constructed teaching geometry. These views illustrate model
preparation, not the output of a generator or a physics simulation.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from animate_projection import font
from animate_gaussian_cabinet import View

OUT=Path(__file__).resolve().parents[1]/'book/assets/simulation-workflow'
TEAL=(108,153,150); BLUE=(91,141,184); GOLD=(219,181,85)
INK='#313a37'; RED='#b95745'; GREEN='#477d68'
SS=2

def box(lo,hi,color):
    return np.array(lo,float),np.array(hi,float),color

from shared_cabinet import PARTS, part_triangles, CabinetMesh
from preview_shared_cabinet import render as raster

def items(group,q=0,omit=()):
    result=[]
    for part in PARTS:
        if part['group']!=group or part['name'] in omit:continue
        part=dict(part)
        if part['kind']=='box':
            part['lo']=np.array(part['lo'])-[0,q,0];part['hi']=np.array(part['hi'])-[0,q,0]
        else:
            part['start']=np.array(part['start'])-[0,q,0];part['end']=np.array(part['end'])-[0,q,0]
        result.append(part)
    return result

def shell(top=True):
    return items('body',omit=() if top else ('body-top','body-upper-frame'))

def drawer(q=.28):return items('drawer',q)

def handle(solid=False):
    # Contact primitives are deliberate simplifications of the same round grip.
    col=(207,216,215)
    if solid:return [box((-.30,-.70,.48),(.30,-.49,.58),col)]
    return [box((-.30,-.70,.48),(.30,-.60,.58),col),
            box((-.246,-.65,.494),(-.174,-.49,.566),col),
            box((.174,-.65,.494),(.246,-.49,.566),col)]

def door():return items('door')

def scene(im,boxes,view,fade=0):
    triangles=[];colors=[];names=[]
    for item in boxes:
        if isinstance(item,dict):p=item
        else:
            lo,hi,color=item;p=dict(kind='box',lo=lo,hi=hi,color=color,name='contact-box')
        ts=part_triangles(p,32);triangles.extend(ts)
        col=np.array(p['color'])*(1-fade)+255*fade
        colors.extend([col]*len(ts));names.extend([p['name']]*len(ts))
    m=CabinetMesh(np.array(triangles),np.array(colors),np.array(['']*len(triangles)),np.array(names))
    view_image=raster(m,size=im.size,eye=view.eye,center=view.center,scale=view.scale,xy=view.xy,ss=1,transparent=True)
    im.paste(view_image,(0,0),view_image)

def label(d,xy,text,size=25,color=INK,bold=False,anchor='mm'):
    d.text(tuple(np.array(xy)*SS),text,font=font(size*SS,bold),fill=color,anchor=anchor)

def line(d,pts,col=INK,width=2):
    d.line([tuple(np.array(p)*SS) for p in pts],fill=col,width=width*SS)

def arrow(d,a,b,col=GREEN,width=3):
    a,b=np.array(a)*SS,np.array(b)*SS;u=(b-a)/np.linalg.norm(b-a);p=np.array([-u[1],u[0]])
    d.line([tuple(a),tuple(b)],fill=col,width=width*SS)
    d.polygon([tuple(b),tuple(b-u*12*SS+p*5*SS),tuple(b-u*12*SS-p*5*SS)],fill=col)

def make_view(scale,center,xy,az=27,el=22):
    return View(scale*SS,center,np.array(xy)*SS,az,el)

def parts():
    im=Image.new('RGB',(1000*SS,610*SS),'white');d=ImageDraw.Draw(im)
    v=make_view(215,(0,-.18,0),(470,306))
    scene(im,shell()+drawer(.40)+door(),v)
    for p,xy,text in [((.61,.05,.05),(795,275),'Body: stays fixed'),
                       ((-.35,-.9,.59),(208,135),'Drawer + handle'),
                       ((-.35,-.9,.59),(208,169),'move together'),
                       ((-.1,-.48,-.38),(205,435),'Door: can rotate')]:
        label(d,xy,text,26)
    line(d,[(655,275),tuple(v((.61,.05,.05))/SS)],TEAL)
    line(d,[(270,195),tuple(v((-.35,-.9,.59))/SS)],BLUE)
    line(d,[(300,420),tuple(v((-.1,-.48,-.38))/SS)],GOLD)
    a=v((.15,-.98,.78))/SS;b=v((.15,-1.40,.78))/SS
    arrow(d,a,b,'#497ba3')
    label(d,(500,560),'A joint lets the drawer slide along one line.',28)
    return im

def cavity(solid=False):
    im=Image.new('RGB',(520*SS,735*SS),'white');d=ImageDraw.Draw(im)
    v=make_view(175,(0,-.10,0),(260,268),32,32)
    boxes=shell(False)+drawer(.24)+door()
    scene(im,boxes,v)
    # Transparent red fill shows an erroneous collision volume, not a wall.
    if solid:
        overlay=Image.new('RGBA',im.size,(0,0,0,0));od=ImageDraw.Draw(overlay)
        lo=np.array([-.54,-.43,-.78]);hi=np.array([.54,.35,.86])
        pts=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
        for ids in [(1,5,7,3),(0,4,5,1),(4,6,7,5)]:
            od.polygon([tuple(p) for p in v(pts[list(ids)])],fill=(185,79,62,65),outline=(185,79,62,255),width=SS)
        im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB');d=ImageDraw.Draw(im)
    label(d,(260,61),'Top removed to show the interior',18)
    label(d,(260,30),'Interior filled' if solid else 'Interior left open',28,RED if solid else GREEN,True)
    # A top-view slice is tied to the same complete cabinet above.
    line(d,[(28,463),(492,463)],'#ddd9cf',1)
    label(d,(260,493),'The same drawer, viewed from above',22)
    # X spans left/right. The front of the cabinet is the bottom of this plan.
    def plan(p):return (260+150*p[0],586-95*p[1])
    def rect(lo,hi,c,outline=None):
        a=plan((lo[0],hi[1]));b=plan((hi[0],lo[1]))
        d.rectangle(tuple(np.array([*a,*b])*SS),fill=c,outline=outline,width=2*SS)
    if solid:rect((-.62,-.43),(.62,.43),'#efd8d1',RED)
    else:
        for lo,hi in [((-.62,-.43),(-.54,.43)),((.54,-.43),(.62,.43)),((-.54,.35),(.54,.43))]:rect(lo,hi,TEAL)
    rect((-.49,-.67),(.49,.03),'#b3cce0','#497ba3')
    rect((-.51,-.73),(.51,-.67),BLUE)
    if solid:
        rect((-.49,-.43),(.49,.03),'#d4998b',RED)
        label(d,(260,566),'Overlap',23,RED,True)
    else:
        label(d,(260,563),'Clear space',23,GREEN,True)
    arrow(d,(375,610),(375,650),'#497ba3')
    label(d,(260,710),'Drawer moves toward us',22)
    return im

def handle_case(solid=False):
    im=Image.new('RGB',(1000*SS,600*SS),'white');d=ImageDraw.Draw(im)
    full=make_view(155,(0,0,0),(205,270),23,18)
    scene(im,shell()+drawer(0)+door(),full)
    pos=full((0,-.65,.53))/SS
    d.rounded_rectangle(tuple(np.array([pos[0]-43,pos[1]-16,pos[0]+43,pos[1]+16])*SS),radius=4*SS,outline='#9a7422',width=2*SS)
    line(d,[(pos[0]+43,pos[1]),(430,175),(495,175)],'#b6a06d')
    panel=box((-.36,-.49,.35),(.36,-.43,.70),BLUE)
    close=make_view(560,(0,-.54,.53),(708,282),38,36)
    finger=box((-.045,-.61,.60 if solid else .50),(.045,-.53,.88),(228,156,94))
    scene(im,[panel]+handle(solid)+[finger],close)
    label(d,(205,470),'Same cabinet',26)
    label(d,(708,55),'Handle contact shape',29,bold=True)
    label(d,(708,448),'Gap filled by one block' if solid else 'Grip + two supports',27,RED if solid else GREEN,True)
    # A finger-shaped probe approaches the gap from above in the drawing.
    gap=close((0,-.57,.70))/SS
    label(d,(510,155),'Finger',24)
    arrow(d,(550,155),gap,RED if solid else GREEN)
    label(d,(708,491),'A finger meets a false solid wall.' if solid else 'The opening behind the grip stays empty.',23)
    label(d,(500,558),'The blue panel and the handle belong to the same drawer.',25)
    return im

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    parts().save(OUT/'cabinet-parts.png')
    cavity(True).save(OUT/'collision-filled.png')
    cavity(False).save(OUT/'collision-open.png')
    handle_case(True).save(OUT/'handle-blocked.png')
    handle_case(False).save(OUT/'handle-open.png')
    # The open shell must not occupy the drawer's internal volume.
    point=np.array([0.,-.1,.55])
    assert not any(np.all(point>p['lo'])&np.all(point<p['hi']) for p in shell())
    gap=np.array([0.,-.56,.53])
    assert not any(np.all(gap>a)&np.all(gap<b) for a,b,c in handle())
    assert all(np.all(gap>a)&np.all(gap<b) for a,b,c in handle(True))
    (OUT/'manifest.json').write_text(json.dumps({'provenance':'Original constructed teaching cabinet, not a reconstruction or physics-engine result.',
        'views':'Depth-buffered views of the shared cabinet. Top removed only in labeled cavity cutaways. Enlarged contact shapes are box approximations of the fixed handle.',
        'checks':'Open shell leaves drawer space empty; three-piece handle leaves finger gap empty; one solid handle box fills it.'},indent=2)+'\n')
    print('Created five cabinet diagrams. Cavity and handle-gap checks passed.')

if __name__=='__main__':main()
