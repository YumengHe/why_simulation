#!/usr/bin/env python3
"""An original cabinet made of illustrative 3D Gaussians, not a fitted result.

All views share fixed centers, covariances, opacities, and colors. The renderer
projects covariance with a perspective Jacobian and composites splats by depth.
Small ellipsoid outlines in the teaching view are shape guides only.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import json
import math
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from animate_projection import font, smooth, warp_plane
from shared_cabinet import gaussians

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'book/assets/projection-cabinet'
W, H, FPS, DURATION = 1280, 900, 24, 64
PAPER = (254, 253, 251)
INK, MUTED, GOLD = '#242923', '#656158', '#9a7422'
BLUE, TEAL, YELLOW = (91, 141, 184), (108, 153, 150), (219, 181, 85)
FOCAL, U, V = 1.3, .34, .45
STAGES = [
    (0, 'Many small blobs make one cabinet',
     'Blue blobs describe the drawer; gold blobs describe the door.',
     'The picture on the right blends their projected colors.'),
    (10, 'Look closely at one blue blob',
     'It is wide along the drawer front, but thin from front to back.',
     'Its color is strongest at the center and fades toward the edge.'),
    (24, 'Project the cabinet onto a flat image',
     'Follow the colored lines from the cabinet to the image plane.',
     'Many overlapping marks combine into the cabinet picture.'),
    (38, 'Move the camera around the same cabinet',
     'The cabinet and all its blobs stay in the same places.',
     'A new camera position gives a new picture of them.'),
    (56, 'One 3D cabinet, different 2D views',
     'Each picture is rendered from the same set of 3D blobs.',
     'No new cabinet is built when we change the view.'),
]


def label(draw, xy, value, size=27, color=INK, bold=False, anchor='mm'):
    draw.text(tuple(xy), value, font=font(size, bold), fill=color, anchor=anchor)


def line(draw, pts, color, width=2):
    draw.line([tuple(p) for p in pts], fill=color, width=width, joint='curve')


# Geometry, dimensions, part ownership and handles come from one source.
_SAMPLES = gaussians(spacing=.085)
NAMES = _SAMPLES.names


def make_cabinet():
    # The fixed per-surface palette supplies shape cues in every representation.
    normal = _SAMPLES.normals
    per_axis = np.where(normal > 0, [.74,.79,1.08], [.83,1.,.68])
    shade = np.sum(normal**2*per_axis,axis=1)
    colors = np.clip(_SAMPLES.colors*255*shade[:,None],0,255)
    return _SAMPLES.centers, _SAMPLES.covariances, colors, _SAMPLES.groups


CENTERS, COVS, COLORS, GROUPS = make_cabinet()
SELECTED = int(np.argmin(np.linalg.norm(CENTERS-np.array([-.31,-.49,.58]),axis=1)))


def camera(angle):
    a = math.radians(angle)
    c = np.array([3.7*math.sin(a),-3.7*math.cos(a),.40])
    forward = -c/np.linalg.norm(c)
    right = np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right)
    up = np.cross(right, forward)
    return c,forward,right,up


def project(means, covs, angle):
    c,f,r,u = camera(angle)
    q = means-c
    depth = q @ f
    x,y = q @ r,q @ u
    uv = FOCAL*np.column_stack((x,y))/depth[:,None]
    jac = FOCAL/depth[:,None,None]*np.stack((r-x[:,None]/depth[:,None]*f,
                                            u-y[:,None]/depth[:,None]*f),axis=1)
    cov = jac @ covs @ jac.transpose(0,2,1)
    return uv,cov,depth


def plane_point(uv,angle):
    c,f,r,u=camera(angle)
    return c+FOCAL*f+uv[0]*r+uv[1]*u


def blend_splats(means,covs,colors,depth,width,height,opacity=.94):
    """Rasterize bounded Gaussian footprints, far to near, on white."""
    out=np.full((height,width,3),255.,dtype=np.float32)
    for i in np.argsort(depth)[::-1]:
        cov=covs[i]+np.eye(2)*.16
        rx,ry=3.5*np.sqrt(np.diag(cov))
        x,y=means[i]
        x0,x1=max(0,int(math.floor(x-rx))),min(width,int(math.ceil(x+rx))+1)
        y0,y1=max(0,int(math.floor(y-ry))),min(height,int(math.ceil(y+ry))+1)
        if x0>=x1 or y0>=y1:continue
        yy,xx=np.mgrid[y0:y1,x0:x1]
        dx,dy=xx-x,yy-y
        a,b,d=cov[0,0],cov[0,1],cov[1,1]
        exponent=(d*dx**2-2*b*dx*dy+a*dy**2)/(a*d-b*b)
        alpha=(opacity*np.exp(-.5*exponent)).astype(np.float32)[...,None]
        patch=out[y0:y1,x0:x1]
        patch[:]=patch*(1-alpha)+colors[i]*alpha
    return Image.fromarray(np.uint8(np.clip(out,0,255))).convert('RGBA')


@lru_cache(96)
def camera_image(angle,width=340,height=450):
    uv,cov,depth=project(CENTERS,COVS,angle)
    scale=np.diag([width/(2*U),-height/(2*V)])
    pixels=uv @ scale.T+np.array([width/2,height/2])
    cov=scale @ cov @ scale.T
    return blend_splats(pixels,cov,COLORS,depth,width,height)


class View:
    def __init__(self,scale=165,center=(0,-1.3,0),xy=(465,442),az=38,el=22):
        a,e=map(math.radians,(az,el))
        self.eye=np.array([math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)])
        self.right=np.array([math.cos(a),math.sin(a),0.])
        self.up=np.cross(self.eye,self.right)
        self.scale,self.center,self.xy=scale,np.array(center),np.array(xy)
        self.matrix=scale*np.array([self.right,-self.up])
    def __call__(self,p):return (np.asarray(p)-self.center)@self.matrix.T+self.xy


@lru_cache(4)
def guide_layer(large=False):
    view=View(225,(0,0,0),(395,439),24,22) if large else View()
    layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
    shadow=view([[x,y,-.9] for x,y in [(-.8,-.55),(.8,-.55),(.8,.7),(-.8,.7)]])
    d.polygon([tuple(p) for p in shadow],fill='#eae8e1')
    mu=view(CENTERS);cov=view.matrix @ COVS @ view.matrix.T
    for i in np.argsort(CENTERS @ view.eye):
        vals,vec=np.linalg.eigh(cov[i]);vals=np.maximum(vals,.2)
        angles=np.linspace(0,2*math.pi,17)
        # Ellipsoidal shape guides, not the actual soft splat boundary.
        pts=np.column_stack((np.cos(angles),np.sin(angles))) @ (vec@np.diag(np.sqrt(vals)*1.05)).T+mu[i]
        color=tuple(int(c) for c in COLORS[i])
        d.polygon([tuple(p) for p in pts],fill=color,outline=tuple(int(.82*c) for c in color))
    return layer


def draw_camera(im,view,angle):
    c,f,r,u=camera(angle);d=ImageDraw.Draw(im)
    vertices=np.array([c+x*f+y*r+z*u for x in (-.30,-.04) for y in (-.16,.16) for z in (-.12,.12)])
    faces=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(1,5,7,3),(0,2,6,4)]
    for ids in sorted(faces,key=lambda ix:vertices[list(ix)].mean(axis=0) @ view.eye):
        shade=.70+.05*faces.index(ids)
        d.polygon([tuple(p) for p in view(vertices[list(ids)])],fill=tuple(round(v*shade) for v in (155,147,125)))
    x,y=view(c);d.ellipse((x-6,y-6,x+6,y+6),fill=GOLD)
    line(d,view([c-.12*f-.12*u,c-.12*f-.50*u]),MUTED,3)
    label(d,(x,y+74),'Camera',23)


def image_panel(im,angle):
    tex=camera_image(round(angle,3));im.alpha_composite(tex,(905,220))
    d=ImageDraw.Draw(im);d.rectangle((905,220,1245,670),outline='#c5b894',width=2)
    label(d,(1075,181),'Camera image',27)


def draw_setup(im,t,angle):
    view=View();d=ImageDraw.Draw(im)
    for x in (-1,0,1):line(d,view([[x,-3.8,-.91],[x,1,-.91]]),'#edeae4',1)
    for y in (-3.5,-2,-.5,1):line(d,view([[-1.2,y,-.91],[1.2,y,-.91]]),'#edeae4',1)
    im.alpha_composite(guide_layer())
    c,f,r,u=camera(angle)
    ray_indices=[SELECTED]
    for target in ([.2,-.49,.4],[-.3,-.485,-.4],[.3,-.485,-.6],[.6,-.2,.6]):
        ray_indices.append(int(np.argmin(np.linalg.norm(CENTERS-np.array(target),axis=1))))
    d=ImageDraw.Draw(im)
    progress=smooth((t-24)/4) if t<38 else 1.
    for i in ray_indices:
        color=tuple(int(v) for v in COLORS[i])
        line(d,view([c,c+(CENTERS[i]-c)*progress]),color,2)
    corners=np.array([plane_point(p,angle) for p in [(-U,V),(U,V),(U,-V),(-U,-V)]])
    warp_plane(im,camera_image(round(angle,3)),view(corners))
    d=ImageDraw.Draw(im);line(d,view(np.vstack([corners,corners[0]])),'#a6936d',3)
    if progress>.99:
        for i in ray_indices:
            uv,_,_=project(CENTERS[i:i+1],COVS[i:i+1],angle)
            x,y=view(plane_point(uv[0],angle));d.ellipse((x-3,y-3,x+3,y+3),fill=tuple(COLORS[i].astype(int)))
    plane_screen=view(corners)
    label(d,(plane_screen[:,0].mean(),plane_screen[:,1].max()+24),'Image plane',23)
    label(d,(595,174),'Fixed 3D cabinet',26)
    draw_camera(im,view,angle);image_panel(im,angle)


def draw_zoom(im,t):
    d=ImageDraw.Draw(im)
    label(d,(340,171),'One drawer blob, enlarged',28)
    # Same covariance as a selected drawer blob, magnified. It is thin in y.
    radii=np.sqrt(np.diag(COVS[SELECTED]));radii=radii/radii.max()
    view=View(145,(0,0,0),(338,424),55,18)
    surface=np.array([[-1.3,.03,-1.3],[1.3,.03,-1.3],[1.3,.03,1.3],[-1.3,.03,1.3]])
    d.polygon([tuple(p) for p in view(surface)],fill='#e5eff5',outline='#b6cbd9')
    tris=[]
    for j in range(20):
        lat0=-math.pi/2+j*math.pi/20;lat1=lat0+math.pi/20
        for k in range(40):
            lon0=k*math.pi/20;lon1=lon0+math.pi/20
            pts=[]
            for lat,lon in ((lat0,lon0),(lat0,lon1),(lat1,lon1),(lat1,lon0)):
                pts.append(radii*np.array([math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat)]))
            pts=np.array(pts);n=np.mean(pts/(radii**2),axis=0);n/=max(np.linalg.norm(n),1e-8)
            shade=.65+.35*max(0,n@np.array([-.3,-.8,.5]))
            tris.append((pts.mean(axis=0)@view.eye,pts,tuple(int(v*shade) for v in BLUE)))
    for _,pts,color in sorted(tris,key=lambda x:x[0]):d.polygon([tuple(p) for p in view(pts)],fill=color)
    for axis in (0,1,2):
        other=[i for i in range(3) if i!=axis];pts=[]
        for a in np.linspace(0,2*math.pi,80):
            p=np.zeros(3);p[other]=radii[other]*[math.cos(a),math.sin(a)];pts.append(p)
        line(d,view(pts),'#789fb9',2)
    label(d,(338,658),'A thin shape near the drawer front',24,color=MUTED)
    # Show an enlarged front-facing footprint; rays are added in the next stage.
    ww,hh=440,370;yy,xx=np.mgrid[0:hh,0:ww]
    alpha=.9*np.exp(-.5*(((xx-ww/2)/90)**2+((yy-hh/2)/85)**2))
    pixels=255*(1-alpha[...,None])+np.array(BLUE)*alpha[...,None]
    tex=Image.fromarray(pixels.astype(np.uint8)).convert('RGBA');im.alpha_composite(tex,(760,245))
    d=ImageDraw.Draw(im);d.rectangle((760,245,1200,615),outline='#dfdbd0',width=2)
    label(d,(980,171),'Its mark, viewed from the front',27)
    d.ellipse((974,424,986,436),outline='white',width=2)
    line(d,[(980,437),(980,496)],'#3d6e96',2);label(d,(980,518),'Strongest at the center',23)
    line(d,[(1095,345),(1140,285)],'#3d6e96',2);label(d,(1040,227),'Fades gradually',23)
    label(d,(980,650),'No sharp cut-off in the color',24,color=MUTED)


def camera_angle(t):
    if t<38:return 0.
    if t<44:return 52*smooth((t-38)/6)
    if t<46:return 52.
    if t<52:return 52-74*smooth((t-46)/6)
    if t<54:return -22.
    return -22+22*smooth((t-54)/2)


def render(t):
    stage=max(i for i,(start,*_) in enumerate(STAGES) if t>=start)
    im=Image.new('RGBA',(W,H),PAPER+(255,));d=ImageDraw.Draw(im)
    if stage==0:
        im.alpha_composite(guide_layer(True));image_panel(im,20)
        d=ImageDraw.Draw(im);label(d,(395,171),'3D blob shapes',28)
        v=View(225,(0,0,0),(395,439),24,22);xy=v(CENTERS[SELECTED])
        d.ellipse((xy[0]-13,xy[1]-13,xy[0]+13,xy[1]+13),outline='white',width=3)
        line(d,[xy+[-15,0],[106,xy[1]]],'#3d6e96',2)
        label(d,(35,xy[1]-24),'One blue blob',23,anchor='lm')
        label(d,(395,678),'Outlines show each blob’s shape',23,color=MUTED)
    elif stage==1:draw_zoom(im,t)
    elif stage in (2,3):draw_setup(im,t,camera_angle(t))
    else:
        for x,angle,name in [(80,-22,'From the left'),(480,0,'From the front'),(880,52,'From the right')]:
            tex=camera_image(angle,320,424);im.alpha_composite(tex,(x,224))
            d=ImageDraw.Draw(im);d.rectangle((x,224,x+320,648),outline='#dfdbd0',width=2)
            label(d,(x+160,181),name,27)
    d=ImageDraw.Draw(im);d.rectangle((0,0,W,118),fill=PAPER)
    label(d,(45,40),f'{stage+1} / 5',25,GOLD,anchor='lm')
    label(d,(45,89),STAGES[stage][1],38,bold=True,anchor='lm')
    d.rectangle((0,708,W,H),fill=PAPER);d.line((45,720,W-45,720),fill='#dfdbd0',width=2)
    label(d,(W/2,766),STAGES[stage][2],29)
    label(d,(W/2,813),STAGES[stage][3],29)
    d.line((45,868,W-45,868),fill='#e8e5de',width=5)
    d.line((45,868,45+(W-90)*t/DURATION,868),fill=GOLD,width=5)
    return im.convert('RGB')


def check():
    assert len(CENTERS)>500 and np.linalg.eigvalsh(COVS).min()>0
    assert GROUPS[SELECTED]=='drawer' and COVS[SELECTED,1,1]<COVS[SELECTED,0,0]/8
    original=CENTERS.copy()
    for angle in (-22,0,52):
        c,f,r,u=camera(angle);basis=np.array([r,u,f]);assert np.allclose(basis @ basis.T,np.eye(3))
        uv,cov,depth=project(CENTERS,COVS,angle)
        assert np.all(depth>0) and np.linalg.eigvalsh(cov).min()>0
        assert np.max(abs(uv[:,0]))<U and np.max(abs(uv[:,1]))<V
        for i in (0,SELECTED,len(CENTERS)-1):
            assert np.linalg.norm(np.cross(plane_point(uv[i],angle)-c,CENTERS[i]-c))<1e-10
    assert np.array_equal(CENTERS,original)
    assert not np.allclose(project(CENTERS,COVS,0)[0],project(CENTERS,COVS,52)[0])
    # A perspective projection halves length and quarters covariance at twice depth.
    c,f,r,u=camera(0);q=np.array([c+3*f,c+6*f]);cv=np.repeat(np.eye(3)[None]*.01,2,axis=0)
    _,pc,_=project(q,cv,0);assert np.allclose(pc[0],4*pc[1])
    # Depth ordering and alpha blending against white.
    pix=blend_splats(np.array([[2,2],[2,2]]),np.repeat(np.eye(2)[None],2,axis=0),
                     np.array([BLUE,YELLOW]),np.array([1,2]),5,5,.5)
    assert np.allclose(np.array(pix)[2,2,:3],.5*np.array(BLUE)+.25*np.array(YELLOW)+.25*255,atol=1)
    print(f'{len(CENTERS)} fixed Gaussians; camera, projection, coverage, thin blob, and blending checks pass.',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stills',action='store_true');parser.add_argument('--check',action='store_true');parser.add_argument('--ffmpeg')
    args=parser.parse_args();check()
    if args.check:return
    OUT.mkdir(parents=True,exist_ok=True)
    for name,t in [('cabinet',4),('one-blob',16),('projection',33),('camera-moved',44),('three-views',60)]:render(t).save(OUT/f'{name}.png')
    if args.stills:return
    encoder=args.ffmpeg or shutil.which('ffmpeg')
    if not encoder:raise SystemExit('Supply --ffmpeg with an installed encoder.')
    command=[encoder,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
             '-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p',
             '-movflags','+faststart',str(OUT/'cabinet-projection.mp4')]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as proc:
        for frame in range(FPS*DURATION):
            proc.stdin.write(render(frame/FPS).tobytes())
            if frame%(FPS*4)==0:print(f'Rendered {frame/FPS:g} / {DURATION} seconds',flush=True)
        proc.stdin.close();code=proc.wait()
    if code:raise SystemExit(code)
    (OUT/'manifest.json').write_text(json.dumps({'duration':DURATION,'fps':FPS,'width':W,'height':H,
        'gaussians':len(CENTERS),'stages':[{'start':s[0],'title':s[1],'captions':s[2:]} for s in STAGES],
        'method':'Fixed analytic scene; projected covariance and depth-sorted alpha blending; no photo fitting.',
        'guide_outlines':'Ellipsoid shape guides; not hard Gaussian boundaries.',
        'camera':'Virtual image plane in front of a pinhole camera. Cabinet stays fixed.',
        'source':'scripts/shared_cabinet.py; original teaching animation, not a trained reconstruction.'},indent=2)+'\n')
    print(f'Wrote {OUT / "cabinet-projection.mp4"}',flush=True)


if __name__=='__main__':main()
