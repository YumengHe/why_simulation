#!/usr/bin/env python3
"""Cabinet field-query and volume-rendering teaching examples.

This is an analytic color/density field, not a trained neural network. Rays
sample the field and use alpha = 1-exp(-sigma*distance), then front-to-back
compositing. No Gaussian splats or triangle rasterization make the images.
The trial field is hand-constructed to illustrate a training comparison.
"""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw

from animate_projection import font
from animate_gaussian_cabinet import camera, View, U, V, FOCAL

OUT=Path(__file__).resolve().parents[1]/'book/assets/nerf-cabinet'
BLUE=np.array([91,141,184],np.float32)/255
TEAL=np.array([108,153,150],np.float32)/255
GOLD=np.array([219,181,85],np.float32)/255
INK='#313a37'; CORAL='#bf644b'; MUTED='#656158'
BOXES=[]


def box(lo,hi,color):
    BOXES.append((np.array(lo,np.float32),np.array(hi,np.float32),np.array(color,np.float32)))


for lo,hi in [((-.62,-.43,-.86),(-.54,.43,.86)),((.54,-.43,-.86),(.62,.43,.86)),
              ((-.54,.35,-.86),(.54,.43,.86)),((-.54,-.43,.79),(.54,.35,.86)),
              ((-.54,-.43,-.86),(.54,.35,-.78))]:box(lo,hi,TEAL)
box((-.51,-.49,.33),(.51,-.43,.74),BLUE)
box((-.51,-.485,-.73),(.51,-.43,.26),GOLD)
box((-.24,-.585,.515),(.24,-.55,.555),np.array([204,210,204])/255)
for x in (-.24,.205):box((x,-.56,.515),(x+.035,-.49,.555),np.array([185,196,192])/255)
box((.345,-.57,-.35),(.385,-.535,-.10),np.array([174,136,51])/255)
for z in (-.35,-.135):box((.345,-.55,z),(.385,-.485,z+.035),np.array([174,136,51])/255)


def field(points,trial=False):
    """Return density and RGB at arbitrary 3D points. No view dependence here."""
    shape=points.shape[:-1]
    density=np.zeros(shape,np.float32);weighted_color=np.zeros((*shape,3),np.float32)
    # A finite soft boundary avoids aliasing, while panels keep hollow spaces.
    width=.025 if trial else .008
    for i,(lo,hi,base) in enumerate(BOXES):
        inside_distance=np.minimum(points-lo,hi-points)
        nearest=np.min(inside_distance,axis=-1)
        occupancy=np.clip((nearest+width)/(2*width),0,1)
        sigma=occupancy*(28 if trial else 100)
        axis=np.argmin(inside_distance,axis=-1)
        upper=points>(lo+hi)/2
        shades=np.where(axis==0,np.where(upper[...,0],.76,.88),
                        np.where(axis==1,np.where(upper[...,1],.78,1.),np.where(upper[...,2],1.06,.70)))
        col=np.array([.56,.58,.57],np.float32) if trial and i==5 else base
        density+=sigma
        weighted_color+=sigma[...,None]*shades[...,None]*col
    colors=weighted_color/np.maximum(density[...,None],1e-8)
    return density,np.clip(colors,0,1)


def trace(origins,directions,near,far,steps=176,trial=False):
    """Actual sampled volume rendering, accumulating in physical ray distance."""
    delta=(far-near)/steps
    trans=np.ones(near.shape,np.float32);rgb=np.zeros((*near.shape,3),np.float32)
    for i in range(steps):
        distance=near+(i+.5)*delta
        p=origins+directions*distance[...,None]
        sigma,color=field(p,trial)
        alpha=-np.expm1(-sigma*delta)
        w=trans*alpha
        rgb+=w[...,None]*color
        trans*=1-alpha
    return np.clip(rgb+trans[...,None],0,1),trans


def render(angle,width=360,height=430,trial=False,camera_setup=None,extent=None):
    c,f,r,u=camera(angle) if camera_setup is None else camera_setup
    half_width,half_height=(U,V) if extent is None else extent
    xx,yy=np.meshgrid((np.arange(width)+.5)/width*2*half_width-half_width,half_height-(np.arange(height)+.5)/height*2*half_height)
    directions=f+xx[...,None]/FOCAL*r+yy[...,None]/FOCAL*u
    directions/=np.linalg.norm(directions,axis=-1)[...,None]
    # Crop each ray to the cabinet's bounding volume; miss rays stay white.
    lo,hi=np.array([-.72,-.69,-.96]),np.array([.72,.53,.96])
    inv=1/np.where(np.abs(directions)>1e-8,directions,1e-8)
    a,b=(lo-c)*inv,(hi-c)*inv
    near=np.max(np.minimum(a,b),axis=-1);far=np.min(np.maximum(a,b),axis=-1)
    hit=far>near
    out=np.ones((height,width,3),np.float32)
    out[hit],_=trace(c,directions[hit].astype(np.float32),near[hit].astype(np.float32),far[hit].astype(np.float32),trial=trial)
    return Image.fromarray(np.uint8(np.round(out*255)))


def label(d,xy,text,size=24,color=INK,bold=False,anchor='mm'):
    d.text(tuple(xy),text,font=font(size,bold),fill=color,anchor=anchor)


def selected_ray():
    c=np.array([0.,-3.,.64]);direction=np.array([0.,1.,0.])
    return c,direction,c+np.array([1.,2.,2.54])[:,None]*direction


def cabinet_guide(d,view):
    faces=[]
    for lo,hi,color in BOXES:
        verts=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
        for ids in ((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(1,5,7,3),(0,2,6,4)):
            pts=verts[list(ids)];faces.append((pts.mean(0)@view.eye,pts,color))
    for _,pts,col in sorted(faces,key=lambda t:t[0]):
        color=tuple(np.uint8((col*.48+.52)*255))
        d.polygon([tuple(p) for p in view(pts)],fill=color,outline='#bacbc3')


def camera_poses():
    im=Image.new('RGB',(1000,650),'white');d=ImageDraw.Draw(im)
    view=View(118,(0,-1.3,0),(500,340),12,45)
    for angle in (-35,0,35):
        c,f,r,u=camera(angle)
        d.line([tuple(p) for p in view([c,np.zeros(3)])],fill='#d3c6a7',width=2)
    cabinet_guide(d,view)
    for angle,name in [(-35,'Photo 1'),(0,'Photo 2'),(35,'Photo 3')]:
        c,*_=camera(angle);x,y=view(c)
        d.rounded_rectangle((x-23,y-16,x+23,y+16),radius=4,fill='#777e76')
        d.ellipse((x-8,y-8,x+8,y+8),fill='#cad1ca')
        label(d,(x,y+43),name,27)
    label(d,(500,50),'Where was the camera for each photograph?',30,bold=True)
    label(d,(500,610),'One cabinet stays still; the camera moves around it.',25)
    return im


def point_inputs():
    im=Image.new('RGB',(1150,700),'white');d=ImageDraw.Draw(im)
    view=View(188,(0,-1.3,0),(510,350),52,22)
    cabinet_guide(d,view)
    c,f,_=selected_ray()
    r,u=np.array([1.,0.,0.]),np.array([0.,0.,1.])
    plane_center=c+.7*f
    corners=np.array([plane_center+x*r+y*u for x,y in [(-.24,-.28),(.24,-.28),(.24,.28),(-.24,.28)]])
    polygon=view(corners)
    d.polygon([tuple(p) for p in polygon],fill='#faf7ef',outline='#9a7422',width=2)
    for x in np.linspace(-.24,.24,6):
        d.line([tuple(p) for p in view([plane_center+x*r-.28*u,plane_center+x*r+.28*u])],fill='#d8cdae',width=1)
    for y in np.linspace(-.28,.28,6):
        d.line([tuple(p) for p in view([plane_center-.24*r+y*u,plane_center+.24*r+y*u])],fill='#d8cdae',width=1)
    d.line([tuple(p) for p in view([c,c+3.45*f])],fill=CORAL,width=4)
    x,y=view(c);d.rounded_rectangle((x-23,y-17,x+23,y+17),radius=4,fill='#777e76')
    label(d,(x,y+48),'Camera',29)
    label(d,(x,y+82),'(0, −3, 0.64)',25)
    x,y=view(plane_center)
    d.ellipse((x-6,y-6,x+6,y+6),fill=CORAL,outline='white',width=2)
    label(d,(x+3,y+137),'Selected pixel',25)
    d.line((x+3,y+116,x+3,y+8),fill='#9a7422',width=1)
    for i,distance in enumerate((1.,2.,2.54),1):
        x,y=view(c+distance*f)
        d.ellipse((x-7,y-7,x+7,y+7),fill='#5b8db8',outline='white',width=2)
        label(d,(x,y-33),f'P{i}',29,color='#426c8f',bold=True)
    label(d,(570,60),'One pixel → one ray → several 3D sample points',30,bold=True)
    label(d,(782,524),'All three queries use direction (0, 1, 0).',25)
    label(d,(782,562),'The 3D positions differ along the ray.',25)
    # Axes are explicitly labeled and follow the same world frame as the table.
    origin=np.array([0.,0.,0.]);base=np.array([130.,570.])
    for vec,name,col in [(r,'X','#b85f52'),(f,'Y','#628268'),(u,'Z','#5b8db8')]:
        delta=view.matrix@vec*.36;end=base+delta
        d.line([tuple(base),tuple(end)],fill=col,width=3)
        unit=delta/np.linalg.norm(delta);perp=np.array([-unit[1],unit[0]])
        d.polygon([tuple(end),tuple(end-unit*10+perp*4),tuple(end-unit*10-perp*4)],fill=col)
        label(d,end+unit*18,name,25,col,True)
    label(d,(145,646),'Axes for this example',22)
    return im


def ray_figure(front):
    im=Image.new('RGB',(1200,700),'white');d=ImageDraw.Draw(im)
    view=View(158,(0,-1.3,0),(382,320),52,22)
    cabinet_guide(d,view)
    c,direction,pts=selected_ray()
    r,u=np.array([1.,0.,0.]),np.array([0.,0.,1.])
    pc=c+.7*direction
    corners=np.array([pc+x*r+y*u for x,y in [(-.24,-.28),(.24,-.28),(.24,.28),(-.24,.28)]])
    d.polygon([tuple(p) for p in view(corners)],fill='#faf7ef',outline='#9a7422',width=2)
    for x in np.linspace(-.24,.24,6):
        d.line([tuple(p) for p in view([pc+x*r-.28*u,pc+x*r+.28*u])],fill='#d8cdae',width=1)
    for z in np.linspace(-.28,.28,6):
        d.line([tuple(p) for p in view([pc-.24*r+z*u,pc+.24*r+z*u])],fill='#d8cdae',width=1)
    d.line([tuple(p) for p in view([c,c+3.45*direction])],fill=CORAL,width=3)
    xy=view(c);d.rounded_rectangle((xy[0]-20,xy[1]-16,xy[0]+20,xy[1]+16),radius=4,fill='#777e76')
    label(d,xy+[0,43],'Camera',26)
    for name,p in zip(('P1','P2','P3'),pts):
        x,y=view(p);d.ellipse((x-7,y-7,x+7,y+7),fill='#5b8db8',outline='white',width=2)
        label(d,(x,y-31),name,28,'#426c8f',True)
    x,y=view(pc);d.rectangle((x-5,y-5,x+5,y+5),fill='#5b8db8',outline=CORAL,width=2)
    label(d,(x+24,y+135),'Selected pixel',25)
    d.line((x+24,y+111,x,y+9),fill='#9a7422',width=1)
    label(d,(390,54),'The same ray and sample positions P1–P3',29,bold=True)
    label(d,(410,524),'P1 and P2: air      P3: blue drawer front',25)
    thumb=front.resize((270,405),Image.Resampling.LANCZOS)
    im.paste(thumb,(895,142))
    d.rectangle((895,142,1165,547),outline='#d8d3c8',width=2)
    x,y=1030,344.5
    d.rectangle((x-6,y-6,x+6,y+6),outline=CORAL,width=3)
    label(d,(1030,99),'Rendered prediction',26,bold=True)
    label(d,(1030,580),'Same selected pixel',24)
    # The camera's central ray corresponds to the marked central image pixel.
    d.line((x+9,y,1178,y,1178,580,1150,580),fill=CORAL,width=1)
    label(d,(600,652),'Sample outputs along this ray combine into one pixel color.',28,bold=True)
    return im


def ray_camera_image():
    c,f,_=selected_ray()
    im=render(0,321,481,camera_setup=(c,f,np.array([1.,0.,0.]),np.array([0.,0.,1.])),extent=(.52,.78))
    assert np.linalg.norm(np.array(im.getpixel((160,240)))/255-BLUE)<.03
    return im


def field_slice():
    """A 3D cutaway sampled on horizontal slices; not a stored voxel grid."""
    w,h=840,570;im=Image.new('RGB',(w,h),'white');d=ImageDraw.Draw(im)
    view=View(215,(0,0,0),(400,275),28,24)
    xs=np.arange(-.64,.65,.035);ys=np.arange(-.60,.46,.035)
    points=np.array([[x,y,z] for z in [-.64,-.29,.12,.47,.68,.82] for y in ys for x in xs])
    sigma,col=field(points)
    occupied=sigma>8
    # These samples make the otherwise implicit field visible to the reader.
    ids=np.flatnonzero(occupied)
    for i in ids[np.argsort(points[ids]@view.eye)]:
        x,y=view(points[i]);color=tuple(np.uint8(col[i]*255))
        d.ellipse((x-2.4,y-2.4,x+2.4,y+2.4),fill=color)
    label(d,(420,36),'Sample the field at locations in 3D',28,bold=True)
    label(d,(420,532),'Colored samples reveal where the panels are.',24)
    return im


def query_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="280" viewBox="0 0 900 280"><rect width="900" height="280" fill="#fefdfb"/><defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#9a7422"/></marker></defs><g font-family="Arial,sans-serif" fill="#313a37" text-anchor="middle"><text x="145" y="72" font-size="25" font-weight="bold">Ask about a 3D spot</text><text x="145" y="120" font-size="23">Position near the</text><text x="145" y="153" font-size="23">blue drawer front</text><text x="145" y="203" font-size="23">+ viewing direction</text><rect x="338" y="60" width="220" height="160" rx="3" fill="#f4efe3" stroke="#c4b17e"/><text x="448" y="110" font-size="25" font-weight="bold">Neural network</text><text x="448" y="153" font-size="22">Its learned settings</text><text x="448" y="184" font-size="22">determine the answer</text><text x="746" y="83" font-size="25" font-weight="bold">Two answers</text><rect x="638" y="114" width="24" height="24" fill="#5b8db8"/><text x="760" y="135" font-size="23">Color: blue</text><text x="746" y="186" font-size="23">Density: high</text></g><g stroke="#9a7422" stroke-width="2" marker-end="url(#a)"><path d="M285 145 H320"/><path d="M577 145 H620"/></g></svg>'''


def checks():
    c,d,points=selected_ray();sigma,color=field(points)
    assert sigma[0]==0 and sigma[1]==0 and sigma[2]>80
    # Front panel blue contribution dominates the matching camera ray.
    rgb,trans=trace(c,d[None],np.array([.5]),np.array([3.6]),steps=480)
    assert np.linalg.norm(rgb[0]-BLUE)<.02 and trans[0]<.01,(rgb,trans)
    # The discrete rule reproduces a uniform medium analytically.
    alpha=-np.expm1(-2*.01);t=(1-alpha)**100
    assert np.isclose(t,np.exp(-2),rtol=1e-12)
    numeric_c=np.array([0.,-3.,.64]);numeric_d=np.array([0.,1.,0.])
    numeric_points=numeric_c+np.array([1.,2.,2.54])[:,None]*numeric_d
    assert np.allclose(numeric_points,[[0,-2,.64],[0,-1,.64],[0,-.46,.64]])
    numeric_density,_=field(numeric_points)
    assert np.all(numeric_density[:2]==0) and numeric_density[2]>80
    return {'sample_densities':sigma.tolist(),'selected_pixel_rgb':rgb[0].tolist(),'remaining_visibility':float(trans[0]),
        'numeric_ray_positions':numeric_points.tolist(),'numeric_ray_densities':numeric_density.tolist()}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    validation=checks();print('Ray and volume-compositing checks passed.',flush=True)
    rendered={}
    for name,angle in [('left',-35),('front',0),('right',35),('new-view',18)]:
        im=render(angle);im.save(OUT/f'{name}.png');rendered[name]=im
        print(f'Rendered {name}.',flush=True)
    render(0,trial=True).save(OUT/'trial-front.png')
    ray_image=ray_camera_image();ray_image.save(OUT/'ray-camera.png')
    ray_figure(ray_image).save(OUT/'one-pixel.png')
    field_slice().save(OUT/'field-samples.png')
    camera_poses().save(OUT/'camera-poses.png')
    point_inputs().save(OUT/'point-inputs.png')
    (OUT/'network-query.svg').write_text(query_svg())
    (OUT/'manifest.json').write_text(json.dumps({
        'provenance':'Original analytic cabinet color/density field. Not a trained NeRF or a recorded training run.',
        'rendering':'176 midpoint samples per intersecting camera ray. Alpha = 1 - exp(-density * sample distance). Front-to-back compositing against white.',
        'input_views_degrees':[-35,0,35],'new_view_degrees':18,
        'trial':'Hand-constructed low-density field with a gray drawer to illustrate comparison with a target image.',
        'field_samples':'Diagnostic samples of an implicit 3D field, not a point-cloud representation or storage format.',
        'validation':validation,
        'numeric_ray_example':{'camera':[0,-3,.64],'direction':[0,1,0],
            'distances':[1,2,2.54],'positions':[[0,-2,.64],[0,-1,.64],[0,-.46,.64]]},
        'pixel_example_camera':{'position':[0,-3,.64],'direction':[0,1,0],
            'samples':['P1','P2','P3'],'central_pixel_matches_query_example':True},
        'references':['https://www.matthewtancik.com/nerf','https://arxiv.org/html/2003.08934v2']
    },indent=2)+'\n')
    print('Cabinet NeRF teaching figures complete.',flush=True)


if __name__=='__main__':main()
