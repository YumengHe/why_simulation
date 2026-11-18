#!/usr/bin/env python3
"""Render an original 3D camera / image-plane lesson as a narrated-by-text MP4.

The external diagram view is orthographic; the illustrated camera is a separate
pinhole camera. Gaussian footprints use its perspective Jacobian and covariance,
with depth-sorted alpha blending. Ellipsoid shells are one-sigma teaching guides,
not hard boundaries of a Gaussian. No trained reconstruction is claimed.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import json
import math
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'book/assets/projection'
W, H, FPS, DURATION = 1280, 900, 24, 52
PAPER = (254, 253, 251)
INK, MUTED, GOLD = '#242923', '#656158', '#9a7422'
COLORS = np.array([[91, 141, 184], [219, 181, 85]], float)
CENTERS = np.array([[4., -.65, 0.], [7., .65, 0.]])
RADII = np.array([.34, .62, .85])
COV = np.diag(RADII**2)
FOCAL, U, V = 1.6, 1., 1.15
UP = np.array([0., 0., 1.])
STAGES = [
    (0, 'A camera, two 3D blobs, and a flat image plane',
     'The rectangle is where the camera image is formed.',
     'We are looking at the whole setup from the outside.'),
    (6, 'Follow the rays to the image plane',
     'Each ray meets the flat plane at an image position.',
     'The nearby blue blob makes a larger mark.'),
    (16, 'Look at the image plane from its edge',
     'Only our view of this diagram is turning.',
     'The flat rectangle now looks like a line.'),
    (26, 'Face the image plane again',
     'It is still a 2D image with width and height.',
     'The 3D blobs have not turned into lines.'),
    (36, 'Move the camera; leave the 3D blobs still',
     'Watch the camera image on the right change.',
     'The same 3D blobs now project to different 2D marks.'),
]


def smooth(t):
    t = np.clip(t, 0., 1.)
    return float(t*t*(3-2*t))


@lru_cache(None)
def font(size, bold=False):
    for path in [f'/System/Library/Fonts/Supplemental/Arial{" Bold" if bold else ""}.ttf',
                 f'/usr/share/fonts/truetype/dejavu/DejaVuSans{"-Bold" if bold else ""}.ttf']:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def camera(angle):
    a = math.radians(angle)
    forward = np.array([math.cos(a), -math.sin(a), 0.])
    horizontal = np.array([-math.sin(a), -math.cos(a), 0.])
    origin = np.array([5., 0., 0.]) - 5*forward
    return origin, forward, horizontal


def camera_projection(p, angle):
    c, forward, horizontal = camera(angle)
    r = np.asarray(p)-c
    depth = r @ forward
    return FOCAL*np.array([r @ horizontal, r @ UP])/depth


def gaussian_projection(mu, angle):
    c, forward, horizontal = camera(angle)
    r = mu-c
    depth, u, v = r @ forward, r @ horizontal, r @ UP
    jac = FOCAL/depth*np.array([horizontal-u/depth*forward, UP-v/depth*forward])
    return FOCAL*np.array([u, v])/depth, jac @ COV @ jac.T, depth


def image_plane_point(uv, angle):
    c, forward, horizontal = camera(angle)
    return c+FOCAL*forward+uv[0]*horizontal+uv[1]*UP


@lru_cache(180)
def camera_image(angle, blue_weight, gold_weight):
    width, height = 320, 368
    uu, vv = np.meshgrid(np.linspace(-U, U, width), np.linspace(V, -V, height))
    grid = np.stack([uu, vv], axis=-1)
    result = np.full((height, width, 3), 255., dtype=float)
    projections = [gaussian_projection(mu, angle) for mu in CENTERS]
    for i in sorted(range(2), key=lambda i: projections[i][2], reverse=True):
        mean, covariance, _ = projections[i]
        diff = grid-mean
        exponent = np.einsum('...i,ij,...j->...', diff, np.linalg.inv(covariance), diff)
        weight = [blue_weight, gold_weight][i]
        alpha = .85*weight*np.exp(-.5*exponent)
        result = result*(1-alpha[..., None])+COLORS[i]*alpha[..., None]
    im = Image.fromarray(np.uint8(np.clip(result, 0, 255))).convert('RGBA')
    return im


class DiagramView:
    def __init__(self, azimuth, elevation, center, scale):
        a, e = map(math.radians, [azimuth, elevation])
        self.eye = np.array([math.sin(a)*math.cos(e), -math.cos(a)*math.cos(e), math.sin(e)])
        self.right = np.array([math.cos(a), math.sin(a), 0.])
        self.up = np.cross(self.eye, self.right)
        self.center, self.scale = np.asarray(center), scale
        self.screen_x = 480.

    def __call__(self, p):
        q = np.asarray(p)-self.center
        return np.stack([self.screen_x+self.scale*(q @ self.right), 425-self.scale*(q @ self.up)], axis=-1)


def text(draw, xy, s, size=27, fill=INK, bold=False, anchor='mm'):
    draw.text(tuple(xy), s, font=font(size, bold), fill=fill, anchor=anchor,
              stroke_width=2, stroke_fill=PAPER)


def line(draw, pts, fill, width=2):
    draw.line([tuple(p) for p in pts], fill=fill, width=width, joint='curve')


def warp_plane(base, texture, corners):
    # Inverse projective map from displayed plane quadrilateral to texture.
    src = np.asarray(corners, float)
    e1, e2 = src[1]-src[0], src[3]-src[0]
    area = abs(e1[0]*e2[1]-e1[1]*e2[0])
    if area < 3:
        return
    lo = np.maximum(np.floor(src.min(axis=0)).astype(int)-2, [0, 0])
    hi = np.minimum(np.ceil(src.max(axis=0)).astype(int)+3, [W, H])
    if np.any(hi <= lo):
        return
    local = src-lo
    targets = [(0, 0), (texture.width-1, 0), (texture.width-1, texture.height-1), (0, texture.height-1)]
    a, b = [], []
    for (x, y), (u, v) in zip(local, targets):
        a.extend([[x,y,1,0,0,0,-u*x,-u*y], [0,0,0,x,y,1,-v*x,-v*y]])
        b.extend([u, v])
    coeffs = np.linalg.solve(np.array(a), np.array(b))
    patch = texture.transform(tuple(hi-lo), Image.Transform.PERSPECTIVE, coeffs,
                              resample=Image.Resampling.BICUBIC)
    base.alpha_composite(patch, tuple(lo))


def blob(base, view, mu, color, opacity):
    layer = Image.new('RGBA', (W, H))
    draw = ImageDraw.Draw(layer)
    triangles = []
    light = np.array([-.3, -.5, 1.]); light /= np.linalg.norm(light)
    def vertex(lat, lon):
        v = np.array([math.cos(lat)*math.cos(lon), math.cos(lat)*math.sin(lon), math.sin(lat)])
        return mu+v*RADII, v/RADII
    for j in range(12):
        a, b = -math.pi/2+j*math.pi/12, -math.pi/2+(j+1)*math.pi/12
        for k in range(24):
            c, d = k*math.pi/12, (k+1)*math.pi/12
            pairs = [vertex(a,c), vertex(a,d), vertex(b,d), vertex(b,c)]
            pts = np.array([p for p,n in pairs])
            n = np.mean([n for p,n in pairs], axis=0)
            n /= max(np.linalg.norm(n), 1e-8)
            shade = .66+.34*max(0, n @ light)
            rgb = tuple(round(float(v)*shade+255*(1-shade)*.3) for v in color)
            triangles.append((pts.mean(axis=0) @ view.eye, view(pts), rgb))
    for _, pts, rgb in sorted(triangles, key=lambda x:x[0]):
        draw.polygon([tuple(p) for p in pts], fill=(*rgb, round(220*opacity)))
    # Three rings give stable 3D shape cues as the diagram rotates.
    for axis in range(3):
        axes = [i for i in range(3) if i != axis]
        pts = []
        for t in np.linspace(0, 2*math.pi, 65):
            v = mu.copy();v[axes[0]] += RADII[axes[0]]*math.cos(t);v[axes[1]] += RADII[axes[1]]*math.sin(t)
            pts.append(view(v))
        line(draw, pts, tuple(int(v*.7) for v in color)+(round(155*opacity),), 2)
    base.alpha_composite(layer)


def phase(t):
    stage = max(i for i, (start, *_) in enumerate(STAGES) if start <= t)
    az, el, center, scale = -42., 18., np.array([3.2,0,0]), 110.
    scene_alpha, inset_alpha, angle = 1., 1., 0.
    if 16 <= t < 26:
        x = smooth((t-16)/5);az *= 1-x;el *= 1-x
    elif 26 <= t < 36:
        x = smooth((t-26)/5);az = -90*x;el = 0
        center = center*(1-x)+np.array([FOCAL,0,0])*x
        scale = 110+95*x;scene_alpha = 1-x;inset_alpha = 1-x
    elif t >= 36:
        x = smooth((t-36)/2)
        az = -90*(1-x)-42*x;el = 18*x
        center = np.array([FOCAL,0,0])*(1-x)+center*x
        scale = 205-95*x;scene_alpha = x;inset_alpha = x
        if t >= 39:
            # Camera turns to either side around the fixed scene, then returns.
            if t < 43:angle = 30*smooth((t-39)/4)
            elif t < 47:angle = 30-60*smooth((t-43)/4)
            else:angle = -30+30*smooth((t-47)/4)
    blue = smooth((t-6)/3)
    gold = smooth((t-9)/3)
    view=DiagramView(az, el, center, scale)
    view.screen_x=480+160*(1-scene_alpha)
    return stage, view, scene_alpha, inset_alpha, angle, blue, gold


def render(t):
    stage, view, scene_alpha, inset_alpha, angle, blue, gold = phase(t)
    im = Image.new('RGBA', (W,H), PAPER+(255,))
    d = ImageDraw.Draw(im)
    c, forward, horizontal = camera(angle)
    # Neutral ground establishes the external observer's view.
    if scene_alpha > .01:
        floor = Image.new('RGBA', (W,H));fd=ImageDraw.Draw(floor)
        for x in range(0,9,2):line(fd,view([[x,-1.7,-1.1],[x,1.7,-1.1]]),(220,217,207,round(130*scene_alpha)))
        for y in (-1.5,0,1.5):line(fd,view([[0,y,-1.1],[8,y,-1.1]]),(220,217,207,round(130*scene_alpha)))
        im.alpha_composite(floor)
        for i in sorted(range(2),key=lambda i:CENTERS[i] @ view.eye):
            blob(im,view,CENTERS[i],COLORS[i],scene_alpha)
        rays=Image.new('RGBA',(W,H));rd=ImageDraw.Draw(rays)
        for i,weight in enumerate([blue,gold]):
            mu=CENTERS[i]
            for offset in ([0,0,RADII[2]],[0,0,-RADII[2]],[0,RADII[1],0],[0,-RADII[1],0]):
                target=mu+offset
                color=tuple(int(v*.8) for v in COLORS[i])+(round(170*weight*scene_alpha),)
                line(rd,view([c,c+(target-c)*weight]),color,2)
        im.alpha_composite(rays)
    # Same texture is shown in the world-space plane and the front-facing inset.
    tex=camera_image(round(angle,3),round(blue,3),round(gold,3))
    world_corners=np.array([image_plane_point(uv,angle) for uv in [(-U,V),(U,V),(U,-V),(-U,-V)]])
    screen_corners=view(world_corners)
    warp_plane(im,tex,screen_corners)
    d=ImageDraw.Draw(im)
    line(d,[*screen_corners,screen_corners[0]],'#a6936d',4)
    # Ray intersections on the plane are shown as dots, not as particle motion.
    if scene_alpha > .01:
        for i,weight in enumerate([blue,gold]):
            for offset in ([0,0,RADII[2]],[0,0,-RADII[2]]):
                point=image_plane_point(camera_projection(CENTERS[i]+offset,angle),angle)
                xy=view(point);r=3
                if weight>.99:d.ellipse((xy[0]-r,xy[1]-r,xy[0]+r,xy[1]+r),fill=tuple(COLORS[i].astype(int)))
        # Camera body and lens are oriented with the camera's forward direction.
        camera_layer=Image.new('RGBA',(W,H));cd=ImageDraw.Draw(camera_layer)
        vertices=np.array([c+x*forward+y*horizontal+z*UP
                           for x in (-.48,-.09) for y in (-.22,.22) for z in (-.18,.18)])
        faces=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(1,5,7,3),(0,2,6,4)]
        for face in sorted(faces,key=lambda ids:vertices[list(ids)].mean(axis=0) @ view.eye):
            shade=.7+.06*faces.index(face)
            cd.polygon([tuple(p) for p in view(vertices[list(face)])],
                       fill=tuple(round(v*shade) for v in (155,147,125))+(round(255*scene_alpha),))
        lens=view(c);cd.ellipse((lens[0]-9,lens[1]-9,lens[0]+9,lens[1]+9),fill=(154,116,34,round(255*scene_alpha)))
        line(cd,view([c-.2*forward-.16*UP,c-.2*forward-.65*UP]),(118,112,93,round(255*scene_alpha)),3)
        im.alpha_composite(camera_layer)
    d=ImageDraw.Draw(im)
    if scene_alpha>.8:
        text(d,view(c)+[0,80],'Camera',26)
        text(d,view(image_plane_point([0,V],angle))+[0,-34],'Image plane',26)
        text(d,view(CENTERS[0]+[0,0,1.22]),'Blue blob',26,fill='#3d6e96')
        text(d,view(CENTERS[1]+[0,0,1.22]),'Gold blob',26,fill='#9a7422')
    elif scene_alpha<.1:
        text(d,(view.screen_x,150),'The image, seen face-on',29)
    if inset_alpha>.01:
        panel=Image.new('RGBA',(W,H));pd=ImageDraw.Draw(panel)
        text(pd,(1100,219),'Camera image',27)
        inset=tex.resize((280,322),Image.Resampling.LANCZOS)
        panel.alpha_composite(inset,(960,250))
        pd.rectangle((960,250,1240,572),outline='#c5b894',width=2)
        text(pd,(1100,604),'A 2D view',25,fill=MUTED)
        if inset_alpha < 1:panel.putalpha(panel.getchannel('A').point(lambda v:round(v*inset_alpha)))
        im.alpha_composite(panel)
    d=ImageDraw.Draw(im)
    # Opaque text regions prevent geometry from crossing the teaching captions.
    d.rectangle((0,0,W,116),fill=PAPER)
    text(d,(45,43),f'{stage+1} / 5',26,GOLD,anchor='lm')
    text(d,(45,89),STAGES[stage][1],38,bold=True,anchor='lm')
    d.rectangle((0,704,W,H),fill=PAPER)
    d.line((45,715,W-45,715),fill='#dfdbd0',width=2)
    text(d,(W/2,766),STAGES[stage][2],31)
    text(d,(W/2,815),STAGES[stage][3],31)
    # Timeline is proportional to video time; no automatic looping.
    d.line((45,868,W-45,868),fill='#e8e5de',width=5)
    d.line((45,868,45+(W-90)*t/DURATION,868),fill=GOLD,width=5)
    return im.convert('RGB')


def check():
    # Independent pinhole expectations and camera orbit invariants.
    assert np.allclose(camera_projection([4,0,1],0),[0,.4])
    assert np.allclose(camera_projection([8,0,1],0),[0,.2])
    a=gaussian_projection(np.array([4,0,0]),0)[1]
    b=gaussian_projection(np.array([8,0,0]),0)[1]
    assert np.allclose(a,4*b)
    for angle in (-30,0,30):
        c,f,h=camera(angle)
        assert abs(f @ h)<1e-12 and np.isclose(np.linalg.norm(f),1)
        for p in CENTERS:
            uv=camera_projection(p,angle);ip=image_plane_point(uv,angle)
            assert np.linalg.norm(np.cross(ip-c,p-c))<1e-10
            assert np.linalg.eigvalsh(gaussian_projection(p,angle)[1]).min()>0
    side=DiagramView(0,0,[3.2,0,0],110)
    corners=side([image_plane_point([u,v],0) for u,v in [(-U,V),(U,V),(U,-V),(-U,-V)]])
    assert np.ptp(corners[:,0])<1e-10 and np.ptp(corners[:,1])>0
    assert not np.allclose(camera_projection(CENTERS[0],-30),camera_projection(CENTERS[0],30))
    print('Projection scale, camera frames, ray intersections, edge-on plane, and moving-camera checks pass.',flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stills',action='store_true')
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--ffmpeg')
    args=parser.parse_args();check()
    if args.check:return
    OUT.mkdir(parents=True,exist_ok=True)
    for name,t in [('setup',3),('rays',13),('edge-on',23),('face-on',33),('camera-moved',43)]:
        render(t).save(OUT/f'{name}.png')
    if args.stills:return
    encoder=args.ffmpeg or shutil.which('ffmpeg')
    if not encoder:raise SystemExit('Supply --ffmpeg with the path to an installed FFmpeg encoder.')
    command=[encoder,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
             '-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast',
             '-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'projection-explained.mp4')]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as proc:
        for frame in range(FPS*DURATION):
            proc.stdin.write(render(frame/FPS).tobytes())
            if frame%(FPS*6)==0:print(f'Rendered {frame/FPS:g} / {DURATION} seconds',flush=True)
        proc.stdin.close();code=proc.wait()
    if code:raise SystemExit(code)
    (OUT/'manifest.json').write_text(json.dumps({'duration':DURATION,'fps':FPS,'width':W,'height':H,
        'stages':[{'start':s[0],'title':s[1],'captions':s[2:]} for s in STAGES],
        'camera':'Pinhole camera; image plane is virtual, in front of the center of projection.',
        'gaussians':'Chosen illustrative covariances; first-order perspective projection, depth-sorted alpha blending.',
        'source':'Original teaching animation; no trained 3DGS result.'},indent=2)+'\n')
    print(f'Wrote {OUT / "projection-explained.mp4"}',flush=True)


if __name__=='__main__':main()
