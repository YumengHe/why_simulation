#!/usr/bin/env python3
"""Render the introductory cabinet loop from the checked-in 45168 mesh.

Triangle drawing and forward kinematics only. No image/video generation model.
The body is fixed; independent prescribed drawer and door positions animate it.
"""
from pathlib import Path
import argparse
import json
import math
import shutil
import subprocess

import numpy as np
from PIL import Image

from draw_urdf_figures import load_geometry, Projection, C
from animate_urdf_examples import rotation, rgb

OUT=Path(__file__).resolve().parents[1]/'book/assets/media'
SIZE, SS, FPS, DURATION = 600, 2, 24, 10


def smooth(t):
    t=max(0.,min(1.,t))
    return (1-math.cos(math.pi*t))/2


def positions(t):
    drawer=.50*(smooth((t-.7)/2.3)-smooth((t-4.2)/2.3))
    door=(math.pi/2)*(smooth((t-2.)/3.)-smooth((t-6.)/3.3))
    return drawer,door


def vertices(data, mesh, t):
    q, angle=positions(t)
    v=np.asarray(mesh['vertices'],float)
    if mesh['link']=='link_0':
        return v+[0,0,q]
    if mesh['link']=='link_1':
        hinge=np.asarray(data['joints']['joint_1']['origin'])
        return (v-hinge)@rotation((0,-1,0),angle).T+hinge
    return v


def render(data, project, t):
    size=SIZE*SS
    pixels=np.full((size,size,3),255,dtype=np.uint8)
    depths=np.full((size,size),-np.inf)
    light=np.array([-.3,.8,1.]); light/=np.linalg.norm(light)
    for mesh in data['meshes']:
        tri=vertices(data,mesh,t)[np.asarray(mesh['faces'])]
        normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-10)
        shades=.75+.25*np.abs(normals@light)
        color=np.array(rgb({'link_0':C['blue'],'link_1':C['gold'],'link_2':C['teal']}[mesh['link']]))
        for triangle,shade in zip(tri,shades):
            xy=np.array([project(v) for v in triangle])*SS
            z=triangle@project.eye
            x0,y0=np.maximum(np.floor(xy.min(axis=0)).astype(int),0)
            x1,y1=np.minimum(np.ceil(xy.max(axis=0)).astype(int)+1,size)
            if x0>=x1 or y0>=y1:continue
            a,b,c=xy
            den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-10:continue
            yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
            wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
            wc=1-wa-wb
            # Orthographic depth varies across each triangle. Comparing it per
            # pixel keeps an inner wall from painting over an outer wall.
            depth=wa*z[0]+wb*z[1]+wc*z[2]
            old=depths[y0:y1,x0:x1]
            visible=(wa>=-1e-9)&(wb>=-1e-9)&(wc>=-1e-9)&(depth>old+1e-9)
            pixels[y0:y1,x0:x1][visible]=np.round(color*shade).astype(np.uint8)
            old[visible]=depth[visible]
    image=Image.fromarray(pixels)
    return image.resize((SIZE,SIZE),Image.Resampling.LANCZOS)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ffmpeg');parser.add_argument('--stills',action='store_true')
    args=parser.parse_args()
    data=load_geometry()
    points=np.concatenate([vertices(data,m,t) for t in np.linspace(0,DURATION,30) for m in data['meshes']])
    project=Projection(points,(45,40,SIZE-90,SIZE-80),yaw=29,pitch=18)
    assert positions(0)==(0,0) and positions(DURATION)==(0,0)
    for mesh in data['meshes']:
        if mesh['link']=='link_2':
            assert np.array_equal(vertices(data,mesh,0),vertices(data,mesh,4))
    OUT.mkdir(parents=True,exist_ok=True)
    render(data,project,0).save(OUT/'cabinet-poster.png')
    if args.stills:
        return
    encoder=args.ffmpeg or shutil.which('ffmpeg')
    if not encoder:
        raise SystemExit('Supply --ffmpeg with an installed encoder.')
    command=[encoder,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
             '-s',f'{SIZE}x{SIZE}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast',
             '-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'cabinet-motion.mp4')]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as proc:
        for i in range(FPS*DURATION):
            proc.stdin.write(render(data,project,i/FPS).tobytes())
            if i%FPS==0:print(f'Cabinet intro: {i/FPS:g}/{DURATION} s',flush=True)
        proc.stdin.close()
        if proc.wait():raise SystemExit('Video encoding failed')
    (OUT/'manifest.json').write_text(json.dumps({
        'generator':'scripts/animate_cabinet_intro.py','source':data['source'],
        'geometry':'scripts/data/cabinet-45168.json','duration':DURATION,'fps':FPS,'size':[SIZE,SIZE],
        'method':'Per-pixel depth-buffered triangle rasterization; prescribed independent joint positions; fixed body and camera.',
        'drawer_range_m':[0,.5],'door_range_degrees':[0,90],
        'limitation':'Forward-kinematics illustration, not a contact simulation.'
    },indent=2)+'\n')


if __name__=='__main__':main()
