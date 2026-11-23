#!/usr/bin/env python3
"""Draw URDF illustrations from the shared procedural teaching cabinet.

An optional --model-dir imports the historical dataset snapshot for inspection.
The normal rendering path uses cabinet_legacy.geometry() from shared_cabinet.
"""
from pathlib import Path
from math import sin, cos, radians, sqrt, pi
from html import escape
import argparse
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'scripts/data/cabinet-45168.json'
OUT = ROOT / 'book/assets/figures'
C = dict(ink='#30352f', muted='#68726a', blue='#5b8db8', teal='#6c9996',
         gold='#dbb555', red='#bf6559', purple='#9680b0', green='#84a16a',
         line='#aab3aa', paper='#fefdfb')


def load_geometry(model_dir=None):
    if model_dir is None:
        from cabinet_legacy import geometry
        return geometry()
    if model_dir:
        root = ET.parse(model_dir / 'mobility.urdf').getroot()
        meshes, joints = [], {}
        for link in root.findall('link'):
            for visual in link.findall('visual'):
                filename = visual.find('geometry/mesh').get('filename')
                vertices, faces, seen = [], [], set()
                for line in (model_dir / filename).read_text().splitlines():
                    fields = line.split()
                    if not fields:
                        continue
                    if fields[0] == 'v':
                        vertices.append([float(x) for x in fields[1:4]])
                    elif fields[0] == 'f':
                        indices = [int(x.split('/')[0]) - 1 for x in fields[1:]]
                        for i in range(1, len(indices)-1):
                            face = [indices[0], indices[i], indices[i+1]]
                            key = tuple(sorted(face))
                            if key not in seen:
                                faces.append(face)
                                seen.add(key)
                origin = [float(x) for x in visual.find('origin').get('xyz', '0 0 0').split()]
                meshes.append(dict(link=link.get('name'), name=visual.get('name'),
                                   file=Path(filename).name, vertices=vertices,
                                   faces=faces, visual_origin=origin))
        for joint in root.findall('joint'):
            joints[joint.get('name')] = dict(
                origin=[float(x) for x in joint.find('origin').get('xyz').split()],
                rpy=[float(x) for x in joint.find('origin').get('rpy', '0 0 0').split()],
                axis=[float(x) for x in joint.find('axis').get('xyz').split()] if joint.find('axis') is not None else None,
            )
        # This asset saves shape points in the body frame. At q=0 these
        # translations cancel; do not assume that for an arbitrary URDF.
        for mesh in meshes:
            if mesh['link'] in ('link_0', 'link_1'):
                joint = joints['joint_'+mesh['link'][-1]]
                assert all(abs(a+b) < 1e-10 for a,b in zip(mesh['visual_origin'], joint['origin']))
        data = dict(source='ArticulateArena sample_data/45168 at 11e49256b8e839f04e5da2f481cbea20c54bc2ce',
                    coordinate_frame='link_2 body frame; meshes in their closed pose',
                    meshes=meshes, joints=joints)
        DATA.parent.mkdir(parents=True, exist_ok=True)
        DATA.write_text(json.dumps(data, separators=(',', ':'))+'\n')
    return json.loads(DATA.read_text())


def dot(a,b): return sum(x*y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(v):
    n=sqrt(dot(v,v))
    return tuple(x/n for x in v) if n else (0,0,0)


class Projection:
    def __init__(self, points, rect, yaw=25, pitch=19):
        y,p=radians(yaw),radians(pitch)
        self.right=(cos(y),0,-sin(y))
        self.up=(-sin(y)*sin(p),cos(p),-cos(y)*sin(p))
        self.eye=(sin(y)*cos(p),sin(p),cos(y)*cos(p))
        xs=[dot(v,self.right) for v in points]
        ys=[-dot(v,self.up) for v in points]
        x,y,w,h=rect
        self.scale=min(w/(max(xs)-min(xs)),h/(max(ys)-min(ys)))
        self.tx=x+w/2-self.scale*(max(xs)+min(xs))/2
        self.ty=y+h/2-self.scale*(max(ys)+min(ys))/2
    def __call__(self,v):
        return (self.tx+self.scale*dot(v,self.right),self.ty-self.scale*dot(v,self.up))


def shade(color, normal):
    light=unit((-.3,.8,1))
    factor=.76+.24*abs(dot(unit(normal),light))
    rgb=[int(color[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{round(c*factor):02x}' for c in rgb)


def paint(meshes, project, appearance, transform=lambda m,v:v):
    faces=[]
    for mesh in meshes:
        color,alpha=appearance(mesh)
        if alpha==0: continue
        vs=[transform(mesh,v) for v in mesh['vertices']]
        for ids in mesh['faces']:
            points=[vs[i] for i in ids]
            normal=cross(sub(points[1],points[0]),sub(points[2],points[0]))
            if dot(normal,project.eye) <= 1e-10: continue
            fill=shade(color,normal)
            coords=' '.join(f'{x:.2f},{y:.2f}' for x,y in map(project,points))
            faces.append((sum(dot(v,project.eye) for v in points)/3,
                          f'<polygon points="{coords}" fill="{fill}" fill-opacity="{alpha}" stroke="{fill}" stroke-opacity="{alpha}" stroke-width=".35" stroke-linejoin="round"/>'))
    return '\n'.join(f[1] for f in sorted(faces,key=lambda f:f[0]))


def label(x,y,lines,anchor='start',color=None):
    if isinstance(lines,str): lines=[lines]
    return '<text x="%s" y="%s" text-anchor="%s" fill="%s" class="callout">%s</text>' % (
        x,y,anchor,color or C['ink'],''.join(f'<tspan x="{x}" dy="{0 if i==0 else 31}">{escape(s)}</tspan>' for i,s in enumerate(lines)))


def path(points,color=C['line'],width=2,dashed=False,arrow=False):
    d='M'+' L'.join(f'{x:.2f},{y:.2f}' for x,y in points)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"'+(' stroke-dasharray="7 6"' if dashed else '')+(f' marker-end="url(#arrow-{color[1:]})"' if arrow else '')+'/>'


def leader(start,bend,target,color=C['line']):
    return path([start,bend,target],color)+f'<circle cx="{target[0]:.2f}" cy="{target[1]:.2f}" r="4" fill="{color}"/>'


def document(title,description,content,height=550):
    markers=''.join(f'<marker id="arrow-{v[1:]}" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="7" markerHeight="7" orient="auto"><path d="M2 2L10 6L2 10" fill="none" stroke="{v}" stroke-width="2" stroke-linejoin="round"/></marker>' for v in C.values())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" viewBox="0 0 760 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<!-- Orthographic projection of the shared teaching cabinet geometry, not a PDF screenshot. -->
<defs>{markers}</defs>
<style>text{{font-family:Arial,Helvetica,sans-serif}}.callout{{font-size:27px;font-weight:500;paint-order:stroke;stroke:#fefdfb;stroke-width:6px;stroke-linejoin:round}}.small{{font-size:23px}}.emphasis{{font-size:29px;font-weight:600}}</style>
<rect width="760" height="{height}" fill="#fefdfb"/>
{content}
</svg>'''


def front(data):
    meshes=[m for m in data['meshes'] if m['link']=='link_0']
    project=Projection([v for m in meshes for v in m['vertices']],(165,110,420,320),yaw=23,pitch=24)
    colors={'original-34.obj':C['red'],'original-36.obj':C['blue'],'original-35.obj':C['green'],
            'original-37.obj':C['purple'],'original-40.obj':C['gold']}
    def style(m):
        if m['file'] in colors:return colors[m['file']],1
        if m['name'].startswith('drawer-handle'):return '#c0b5a2',1
        return '#b4c7ca',.22
    body=paint(meshes,project,style)
    callouts=[
        (365,54,'Top strip','middle',C['red'],(365,65),(365,98),(0,.71,.49)),
        (24,255,'Side strip','start',C['purple'],(141,266),(158,266),(-.47,.53,.49)),
        (588,228,'Side strip','start',C['green'],(591,239),(564,261),(.47,.53,.49)),
        (550,389,['Center','panel'],'start',C['gold'],(543,398),(495,398),(.06,.53,.49)),
        (55,469,'Bottom strip','start',C['blue'],(210,462),(256,436),(0,.36,.49)),
    ]
    for x,y,words,align,color,start,bend,point in callouts:
        body+=leader(start,bend,project(point),color)+label(x,y,words,align)
    OUT.joinpath('drawer-front-meshes.svg').write_text(document('Five shapes in one drawer front','The shared drawer is shown with five colored front shapes: a top strip, a bottom strip, two side strips, and a center panel. All belong to one moving drawer link.',body,520))


def sliding(data):
    meshes=data['meshes']; limit=.76
    origin=data['joints']['joint_0']['origin']
    def moved(m,v): return (v[0],v[1],v[2]+(limit if m['link']=='link_0' else 0))
    project=Projection([moved(m,v) for m in meshes for v in m['vertices']],(160,100,450,360),yaw=32,pitch=20)
    def style(m):
        if m['link']=='link_0':return C['blue'],.9
        if m['link']=='link_1':return '#c7c9bf',.12
        return C['teal'],.12
    body=paint(meshes,project,style,moved)
    closed=[(-.51,.33,.49),(.51,.33,.49),(.51,.74,.49),(-.51,.74,.49),(-.51,.33,.49)]
    body+=path([project(v) for v in closed],C['blue'],2,True)
    start=project(origin); end=project((origin[0],origin[1],origin[2]+limit))
    body+=path([start,end],C['red'],4,arrow=True)
    body+=f'<circle cx="{start[0]:.2f}" cy="{start[1]:.2f}" r="6" fill="{C["red"]}"/>'
    body+=leader((400,65),(400,95),((start[0]+end[0])/2,(start[1]+end[1])/2),C['red'])+label(380,52,'Sliding direction','middle')
    body+=leader((136,180),(169,180),project((-.1,.53,.51+limit)),C['blue'])+label(22,152,['Drawer','q = 76 cm'])
    body+=leader((589,190),(560,190),project((.37,.2,-.1)),C['teal'])+label(584,157,['Cabinet','body'])
    body+=leader((571,390),(538,365),start,C['red'])+label(570,399,['Joint start','(closed)'])
    OUT.joinpath('drawer-prismatic-joint.svg').write_text(document('The drawer slides from closed to 76 centimeters open','Blue drawer at q = 76 centimeters, the upper limit of its prismatic joint. A dashed outline marks its closed position. A red arrow begins at the closed joint origin and points outward along the sliding direction.',body,500))


def rotating(data):
    meshes=data['meshes']; origin=data['joints']['joint_1']['origin']
    def rotate(v,q):
        x,y,z=sub(v,origin)
        return (origin[0]+cos(q)*x-sin(q)*z,origin[1]+y,origin[2]+sin(q)*x+cos(q)*z)
    def moved(m,v):return rotate(v,pi/2) if m['link']=='link_1' else v
    project=Projection([moved(m,v) for m in meshes for v in m['vertices']],(180,85,420,350),yaw=24,pitch=16)
    def style(m):
        if m['link']=='link_1':return C['gold'],.95
        if m['link']=='link_0':return C['blue'],.14
        return C['teal'],.11
    body=paint(meshes,project,style,moved)
    closed=[(-.51,-.73,.49),(.51,-.73,.49),(.51,.26,.49),(-.51,.26,.49),(-.51,-.73,.49)]
    body+=path([project(v) for v in closed],C['gold'],2,True)
    low=(origin[0],origin[1]-.05,origin[2]); high=(origin[0],.40,origin[2])
    body+=path([project(high),project(low)],C['purple'],4,arrow=True)
    a=project(origin)
    body+=f'<circle cx="{a[0]:.2f}" cy="{a[1]:.2f}" r="5.5" fill="{C["purple"]}"/>'
    curve=[project(rotate((origin[0]+.65,origin[1]-.13,origin[2]),pi/2*i/30)) for i in range(31)]
    body+=path(curve,C['gold'],3,arrow=True)
    body+=leader((172,93),(228,93),project((origin[0],.16,origin[2])),C['purple'])+label(24,84,['Hinge axis'])
    body+=leader((158,272),(191,272),project(rotate((.10,-.12,.51),pi/2)),C['gold'])+label(22,253,['Door','q = 90°'])
    body+=leader((581,282),(544,282),project((.31,-.1,.51)),C['gold'])+label(578,267,['Closed','position'])
    OUT.joinpath('door-revolute-joint.svg').write_text(document('The door rotates from closed to 90 degrees open','The shared door is shown at q = 90 degrees, the upper limit of its revolute joint. The purple line is the hinge axis. A dashed gold rectangle marks the closed position and a curved arrow shows the opening direction.',body,500))


def shelf(data):
    meshes=data['meshes']
    project=Projection([v for m in meshes for v in m['vertices']],(190,75,380,355),yaw=29,pitch=20)
    def style(m):
        if m['file']=='original-2.obj':return C['gold'],1
        if m['link']=='link_0':return C['blue'],.08
        if m['link']=='link_1':return '#b7c0b8',.035
        return C['teal'],.085
    body=paint(meshes,project,style)
    body+=leader((139,248),(212,248),project((.06,.30,.2)),C['gold'])+label(30,237,'Shelf')
    body+=leader((581,137),(552,154),project((.38,.5,-.35)),C['teal'])+label(579,106,['Cabinet','body'])
    body+=f'<path d="M60 450H700" stroke="#e1e0d7"/>'
    body+='<text x="60" y="491" class="emphasis" fill="#30352f">visual</text><text x="60" y="525" class="small" fill="#68726a">The surface you see</text>'
    body+='<text x="395" y="491" class="emphasis" fill="#30352f">collision</text><text x="395" y="525" class="small" fill="#68726a">The surface objects touch</text>'
    OUT.joinpath('body-shelf-visual.svg').write_text(document('One shelf shape, used for appearance and contact','The cabinet is transparent to reveal the orange shelf. In this model its visible and collision representations use the same shelf geometry.',body,565))


def base_comparison(data):
    meshes=data['meshes']
    roll,pitch,yaw=data['joints']['joint_2']['rpy']
    def fixed_rotation(v):
        x,y,z=v
        y,z=cos(roll)*y-sin(roll)*z,sin(roll)*y+cos(roll)*z
        x,z=cos(pitch)*x+sin(pitch)*z,-sin(pitch)*x+cos(pitch)*z
        x,y=cos(yaw)*x-sin(yaw)*y,sin(yaw)*x+cos(yaw)*y
        return x,y,z
    # All three panels share a Z-up scene and camera. Map that scene into
    # the renderer's Y-up camera convention; do not rotate each panel's axes.
    def world_to_view(v):return (-v[1],v[2],-v[0])
    transforms=[lambda m,v:world_to_view(fixed_rotation(v)),
                lambda m,v:world_to_view(v),
                lambda m,v:world_to_view(fixed_rotation(v))]
    sets=[[fn(m,v) for m in meshes for v in m['vertices']] for fn in transforms]
    projections=[Projection(vs,(30+250*i,60,200,245),yaw=25,pitch=18) for i,vs in enumerate(sets)]
    scale=min(p.scale for p in projections)
    for i,(p,vs) in enumerate(zip(projections,sets)):
        xs=[dot(v,p.right) for v in vs]; ys=[-dot(v,p.up) for v in vs]
        p.scale=scale; p.tx=130+250*i-scale*(min(xs)+max(xs))/2; p.ty=305-scale*max(ys)
    def style(m):
        if m['link']=='link_0':return C['blue'],1
        if m['link']=='link_1':return C['gold'],1
        return C['teal'],1
    body=''
    for p,fn in zip(projections,transforms):body+=paint(meshes,p,style,fn)
    body+=label(130,352,['Keep base','+ fixed joint'],'middle')
    body+=label(380,352,['Remove both','No extra rotation'],'middle')
    body+=label(630,352,['Remove both','Rotate in scene'],'middle')
    OUT.joinpath('base-fixed-joint.svg').write_text(document('Removing both elements requires restoring the intended orientation','Three starting poses in the same Z-up scene and camera. Left: keep the base and fixed joint. Middle: remove both and use the body as root without replacing the stored rotation; the cabinet starts sideways. Right: also remove both, then rotate the whole model in the scene by the original fixed-joint rotation; the cabinet starts upright. These are starting orientations, not a physics simulation.',body,435))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model-dir',type=Path)
    args=parser.parse_args()
    data=load_geometry(args.model_dir)
    OUT.mkdir(parents=True,exist_ok=True)
    for draw in (front,sliding,rotating,shelf,base_comparison):draw(data)
    print('Drew 5 URDF figures from cabinet geometry.')


if __name__=='__main__':main()
