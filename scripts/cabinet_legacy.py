"""The shared cabinet expressed in the lesson's X-right/Y-up/Z-front frame.

Only the coordinate system and mesh filenames change. Geometry comes solely
from shared_cabinet; this adapter preserves the existing URDF teaching flow.
"""
from pathlib import Path
import json, math, zipfile
import xml.etree.ElementTree as ET
import numpy as np
from shared_cabinet import PARTS, part_triangles, DRAWER_LIMIT, DOOR_LIMIT
OUT=Path(__file__).resolve().parents[1]/'book/assets/cabinet-model/teaching-urdf'
LINKS={'body':'link_2','drawer':'link_0','door':'link_1'}
ORIGINS={'body':np.zeros(3),'drawer':np.array([0.,.53,.46]),'door':np.array([-.51,-.73,.46])}

def geometry():
    meshes=[]
    for part in PARTS:
        tris=part_triangles(part,32)[...,[0,2,1]].copy();tris[...,2]*=-1
        vertices={};faces=[]
        for tri in tris:
            face=[]
            for p in tri:
                key=tuple(np.round(p,10))
                if key not in vertices:vertices[key]=len(vertices)
                face.append(vertices[key])
            faces.append(face)
        filename=part.get('original_file',part['name']+'.obj')
        if part['name']=='body-divider-shelf':filename='original-2.obj'
        meshes.append(dict(link=LINKS[part['group']],name=part['name'],file=filename,
            vertices=list(vertices),faces=faces,visual_origin=(-ORIGINS[part['group']]).tolist(),color=part['color']))
    return dict(source='Shared procedural teaching cabinet: scripts/shared_cabinet.py',
        coordinate_frame='link_2 body frame: X right, Y up, Z front. Closed pose.',meshes=meshes,
        joints={'joint_0':dict(origin=ORIGINS['drawer'].tolist(),rpy=[0,0,0],axis=[0,0,1]),
        'joint_1':dict(origin=ORIGINS['door'].tolist(),rpy=[0,0,0],axis=[0,-1,0]),
        'joint_2':dict(origin=[0,0,0],rpy=[math.pi/2,0,-math.pi/2],axis=None)})

def export():
    data=geometry();(OUT/'textured_objs').mkdir(parents=True,exist_ok=True)
    robot=ET.Element('robot',name='shared_teaching_cabinet')
    robot.append(ET.Comment('Same geometry as the book cabinet, expressed in the Y-up body frame used by this URDF lesson. Fixed handles; 2 DOF.'))
    def vec(v):return ' '.join(f'{x:.8g}' for x in v)
    ET.SubElement(robot,'link',name='base')
    for link in ('link_2','link_0','link_1'):
        node=ET.SubElement(robot,'link',name=link)
        for m in data['meshes']:
            if m['link']!=link:continue
            lines=['# Shared cabinet component; saved in parent body coordinates']
            lines+=['v '+vec(v) for v in m['vertices']]
            lines+=['f '+' '.join(str(i+1) for i in f) for f in m['faces']]
            (OUT/'textured_objs'/m['file']).write_text('\n'.join(lines)+'\n')
            for kind in ('visual','collision'):
                obj=ET.SubElement(node,kind,name=m['name'])
                ET.SubElement(obj,'origin',xyz=vec(m['visual_origin']),rpy='0 0 0')
                geom=ET.SubElement(obj,'geometry');ET.SubElement(geom,'mesh',filename='textured_objs/'+m['file'])
                if kind=='visual':
                    mat=ET.SubElement(obj,'material',name=m['name']+'-color');ET.SubElement(mat,'color',rgba=vec([v/255 for v in m['color']]+[1]))
    for name,parent,child,kind,limit in [('joint_2','base','link_2','fixed',None),('joint_0','link_2','link_0','prismatic',DRAWER_LIMIT),('joint_1','link_2','link_1','revolute',math.radians(DOOR_LIMIT))]:
        j=data['joints'][name];node=ET.SubElement(robot,'joint',name=name,type=kind)
        ET.SubElement(node,'parent',link=parent);ET.SubElement(node,'child',link=child)
        ET.SubElement(node,'origin',xyz=vec(j['origin']),rpy=vec(j['rpy']))
        if j['axis']:
            ET.SubElement(node,'axis',xyz=vec(j['axis']));ET.SubElement(node,'limit',lower='0',upper=str(limit),effort='100',velocity='1')
    ET.indent(robot,space='  ');ET.ElementTree(robot).write(OUT/'cabinet.urdf',encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(OUT.parent/'teaching-cabinet-urdf.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in OUT.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(OUT))
    print('Exported the shared cabinet in the URDF lesson coordinate frame.')
if __name__=='__main__':export()
