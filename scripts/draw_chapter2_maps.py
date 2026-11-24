#!/usr/bin/env python3
"""Generate the Chapter 2 concept maps from explicit SVG shapes and text.

These are authored vector diagrams, not model-generated images. The taxonomy
separates stored elements from field meanings without treating them as exclusive:
a grid can store samples of a field. The workflow marks scene fitting separately
from pretrained generation and allows methods to support several representations.
"""
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parents[1] / 'book/assets/diagrams'
INK, MUTED, LINE = '#293632', '#5f6862', '#dedfd7'
TEAL, BLUE, GOLD = '#528b82', '#447ca4', '#a67a20'

class Diagram:
    def __init__(self, height, title, description):
        self.height = height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}" role="img">',
                      f'<title>{escape(title)}</title><desc>{escape(description)}</desc>',
                      '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 1L9 5L0 9" fill="none" stroke="#64736c" stroke-width="1.5"/></marker></defs>',
                      f'<rect width="960" height="{height}" fill="#fffefa"/>']
    def box(self,x,y,w,h,fill='white',stroke=LINE):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
    def text(self,x,y,lines,size=21,color=INK,bold=False,anchor='start',gap=29):
        if isinstance(lines,str): lines=[lines]
        for i,line in enumerate(lines):
            self.parts.append(f'<text x="{x}" y="{y+i*gap}" text-anchor="{anchor}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{600 if bold else 400}" fill="{color}">{escape(line)}</text>')
    def path(self,d,dashed=False,arrow=True,color='#64736c'):
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"'+(' stroke-dasharray="7 6"' if dashed else '')+(' marker-end="url(#arrow)"' if arrow else '')+'/>')
    def write(self,name):
        (OUT/(name+'.svg')).write_text('\n'.join(self.parts+['</svg>'])+'\n')

def classification():
    d=Diagram(770,'Ways to describe the same 3D cabinet','Stored elements include points, faces, voxel cells and Gaussians. Spatial fields answer questions about distance, occupancy, or color and density. Field meaning and storage can be combined.')
    d.text(36,49,'Ways to describe the same 3D cabinet',30,bold=True)
    d.text(36,84,'Representation = the information kept about the object',21,MUTED)
    d.box(28,112,440,555,'#f3f8f6')
    d.box(492,112,440,555,'#f4f7fb')
    d.text(50,151,'Stored elements',25,TEAL,True)
    d.text(514,151,'Fields: ask about a location',25,BLUE,True)
    entries=[('Point cloud',['3D positions; optional colors'],202),
             ('Mesh',['Vertices + connected faces','Triangle or quad faces'],299),
             ('Voxel grid',['Values in small 3D cells','For example: occupied or empty'],425),
             ('3D Gaussians',['Positions, sizes, orientations,','opacities, and appearance'],551)]
    for title,lines,y in entries:
        d.text(50,y,title,24,INK,True);d.text(50,y+32,lines,20,MUTED,gap=27)
    fields=[('Signed distance (SDF)',['How far from the surface?','Which side: inside or outside?'],202),
            ('Occupancy',['Is this location inside the solid?','Or: how likely is it to be inside?'],340),
            ('Radiance field',['Density + view-dependent color','NeRF: a neural-network example'],478)]
    for title,lines,y in fields:
        d.text(514,y,title,24,INK,True);d.text(514,y+32,lines,20,MUTED,gap=27)
    d.text(514,612,'3D position → field value',21,BLUE,True)
    d.text(36,711,'Storage and field meaning can be combined.',22,INK,True)
    d.text(36,744,'Example: a voxel grid stores sampled distance or occupancy values.',20,MUTED)
    d.write('representation-map')

def workflow():
    d=Diagram(1000,'From photographs or a prompt to a 3D asset and a rendered view','Reconstruction and generation produce supported representations. A compatible renderer and camera make a 2D image. During original 3DGS and NeRF fitting, rendering, comparing to photographs and updating the representation repeat.')
    d.text(36,49,'Create 3D data, then render a view',30,bold=True)
    d.text(36,84,'A method can support more than one representation.',21,MUTED)
    # Two creation routes; independent alternatives, not a serial model chain.
    d.box(36,112,424,98,'#f3f8f6');d.box(500,112,424,98,'#fbf6e9')
    d.text(58,151,'Photographs of the cabinet',24,TEAL,True)
    d.text(58,184,'Observed views of the same scene',20,MUTED)
    d.text(522,151,'An image or a prompt',24,GOLD,True)
    d.text(522,184,'A condition for a pretrained generator',20,MUTED)
    d.path('M248 210V241');d.path('M712 210V241')
    d.box(36,246,424,167,'white',TEAL);d.box(500,246,424,167,'white',GOLD)
    d.text(58,282,'Reconstruction',25,TEAL,True)
    d.text(58,315,['COLMAP / DUSt3R / VGGT','Cameras + geometry; further routes:','surface meshes, 3DGS, or NeRF'],20,gap=29)
    d.text(522,282,'Generation',25,GOLD,True)
    d.text(522,315,['Example: TRELLIS','Uses prior training to propose an asset','with one or more supported outputs'],20,gap=29)
    d.path('M248 413V444H480V472');d.path('M712 413V444H480',arrow=False)
    d.box(130,478,700,100,'#f3f8f6',TEAL)
    d.text(480,518,'3D representation',26,TEAL,True,'middle')
    d.text(480,551,'For example: points, a mesh, Gaussians, or a field',21,INK,anchor='middle')
    d.path('M480 578V622')
    d.box(130,628,700,100,'#f4f7fb',BLUE)
    d.text(480,667,'Compatible renderer + chosen camera',25,BLUE,True,'middle')
    d.text(480,700,'Calculate a picture from this viewpoint',21,INK,anchor='middle')
    d.path('M480 728V769')
    d.box(260,775,440,73)
    d.text(480,821,'2D image of the cabinet',24,INK,True,'middle')
    d.box(36,880,888,89,'#faf8f1',GOLD)
    d.text(58,912,'During 3DGS / NeRF fitting:',21,GOLD,True)
    d.text(58,947,'Render → compare with input photos → update the 3D representation → repeat',21)
    d.path('M700 811H886V917',dashed=True)
    d.path('M36 924H15V528H123',dashed=True)
    d.write('reconstruction-workflow')

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    classification();workflow()
    print('Generated two Chapter 2 vector maps.')
