#!/usr/bin/env python3
"""UV-Net and AutoMate teaching plates from the canonical cabinet.

Authored geometry/graphs, not trained-model predictions or a CAD-kernel run.
"""
from pathlib import Path
from types import SimpleNamespace
import json, math
import numpy as np
from PIL import Image, ImageDraw
from preview_shared_cabinet import render, font
from shared_cabinet import mesh, PART_BY_NAME, part_triangles
OUT=Path(__file__).resolve().parents[1]/'book/assets/cad-learning'
PAPER='#fefdfb';INK='#292b29';MUTED='#69675f';TEAL='#528682';GOLD='#a87a20';BLUE='#4e83a7';LINE='#dddcd4'
EYE=np.array([3.,-6.,2.6]);EYE/=np.linalg.norm(EYE)
RIGHT=np.cross([0,0,1],EYE);RIGHT/=np.linalg.norm(RIGHT);UP=np.cross(EYE,RIGHT)
class Plate:
 def __init__(self,h):self.im=Image.new('RGB',(1200,2*h),PAPER);self.d=ImageDraw.Draw(self.im)
 def text(self,x,y,s,size=20,color=INK,bold=False,anchor='ls'):
  self.d.text((2*x,2*y),s,font=font(2*size,bold),fill=color,anchor=anchor)
 def line(self,points,color=LINE,width=2):self.d.line([(2*x,2*y) for x,y in points],fill=color,width=width*2)
 def arrow(self,a,b,color=GOLD):
  self.line([a,b],color);v=np.array(b)-a;v=v/np.linalg.norm(v);n=np.array([-v[1],v[0]])
  self.line([np.array(b)-9*v+4*n,b,np.array(b)-9*v-4*n],color)
 def dot(self,p,r=3,color=GOLD):
  x,y=p;self.d.ellipse((2*(x-r),2*(y-r),2*(x+r),2*(y+r)),fill=color)
 def rule(self,y):self.line([(24,y),(576,y)])
 def picture(self,im,x,y):self.im.paste(im,(2*x,2*y))
 def save(self,name):self.im.save(OUT/(name+'.png'),optimize=True)
def parts_model(mode='grip',offset=0):
 tri=[];colors=[]
 for name,p in PART_BY_NAME.items():
  use=(name=='drawer-handle-grip') if mode=='grip' else (name.startswith('drawer-handle') or name.startswith('drawer-front'))
  if not use:continue
  t=part_triangles(p,64);c=np.tile(p['color'],(len(t),1)).astype(float)
  if mode=='grip':
   c[:]=[138,179,176];c[np.arange(len(t))%4>=2]=[217,173,89]
  if name.startswith('drawer-handle'):t=t+[0,-offset,0]
  tri.extend(t);colors.extend(c)
 return SimpleNamespace(triangles=np.array(tri),colors=np.array(colors))
def scene(model,w,h,center,scale):
 im=render(model,size=(w*2,h*2),center=center,scale=scale*2,ss=2)
 def project(p):
  p=np.array(p)-center;return np.array([w/2+scale*p@RIGHT,h/2-scale*p@UP])
 return im,project

def handle_model(labeled=False):
 """Canonical grip/support surfaces with authored teaching labels."""
 triangles=[];colors=[]
 for name,part in PART_BY_NAME.items():
  if not name.startswith('drawer-handle'):continue
  t=part_triangles(part,64)
  color=([104,163,159] if name.endswith('grip') else [219,174,78]) if labeled else [207,216,215]
  triangles.extend(t);colors.extend([color]*len(t))
 return SimpleNamespace(triangles=np.array(triangles),colors=np.array(colors))

def uvnet():
 p=Plate(580)
 p.text(24,29,'UV-NET  /  TEACHING EXAMPLE',14,GOLD)
 p.text(24,65,'Recognize the handle and its faces',26,bold=True)
 p.text(24,106,'01  Input: an existing CAD handle',22,bold=True)
 center=np.array([0,-.59,.53])
 im,q=scene(handle_model(),270,110,center,430);p.picture(im,16,119)
 p.text(310,158,'The grip and two supports',18)
 p.text(310,188,'already have a shape.',18,MUTED)
 p.rule(241)
 p.text(24,278,'02  Read the CAD geometry',22,bold=True)
 p.text(24,309,'Use surface samples and shared boundaries to recognize shape.',17,MUTED)
 p.rule(332)
 p.text(24,369,'03  Two possible kinds of output',22,bold=True)
 p.text(30,403,'A class for the whole part',18,TEAL,True)
 p.text(320,403,'A label for each face',18,TEAL,True)
 for x,labeled in [(16,False),(310,True)]:
  im,q=scene(handle_model(labeled),270,95,center,420);p.picture(im,x,408)
 p.text(150,530,'“Handle”',22,INK,True,anchor='ms')
 p.dot((325,516),5,TEAL);p.text(340,522,'Grip surface',17)
 p.dot((325,541),5,GOLD);p.text(340,547,'Support surface',17)
 p.text(300,575,'Illustrative labels; a model must be trained for these categories.',16,MUTED,anchor='ms')
 p.save('uvnet')

def automate():
 p=Plate(790)
 p.text(24,31,'AUTOMATE  /  ASSEMBLE EXISTING CAD PARTS',14,GOLD)
 p.text(24,66,'Suggest how the handle attaches',26,bold=True)
 p.text(24,108,'01  Select parts and nearby mounting faces',21,bold=True)
 # Disassembled front and handle, with selected mounting regions highlighted.
 im,q=scene(parts_model('mount',.26),550,220,np.array([0,-.63,.56]),340)
 p.picture(im,25,118)
 for x in (-.21,.21):
  a=np.array([25,118])+q([x,-.75,.53]);b=np.array([25,118])+q([x,-.49,.53])
  p.dot(a,5,GOLD);p.dot(b,5,GOLD);p.arrow(a,b,GOLD)
 p.text(300,359,'Gold: candidate mounting regions on the two parts',18,MUTED,anchor='ms')
 p.rule(380);p.text(24,414,'02  Use geometry and B-rep connections',21,bold=True)
 for x,txt in [(115,'Face'),(300,'Boundary edges'),(485,'Vertices')]:
  p.dot((x,457),8,TEAL);p.text(x,491,txt,18,MUTED,anchor='ms')
 p.line([(123,457),(292,457)],TEAL);p.line([(308,457),(477,457)],TEAL)
 p.text(300,522,'Read surface types, parameters, and connected entities.',18,MUTED,anchor='ms')
 p.rule(545);p.text(24,579,'03  Rank suggestions; the user chooses',21,bold=True)
 im,q=scene(parts_model('mount'),320,140,np.array([0,-.55,.56]),220);p.picture(im,16,601)
 p.text(365,642,'Example choice:',19,MUTED)
 p.text(365,673,'Fixed connection',21,TEAL,True)
 p.text(365,703,'Handle stays on drawer.',16,MUTED)
 p.text(300,772,'The CAD assembly keeps the selected relationship.',19,MUTED,anchor='ms')
 p.save('automate')
 # The authored target places both support end centers on the drawer-front plane.
 front=PART_BY_NAME['drawer-front-center']['lo'][1]
 assert all(math.isclose(PART_BY_NAME['drawer-handle-'+side+'-support']['start'][1],front) for side in ['left','right'])

def main():
 OUT.mkdir(parents=True,exist_ok=True);uvnet();automate()
 (OUT/'manifest.json').write_text(json.dumps({'generator':'scripts/draw_cad_learning.py','geometry':'scripts/shared_cabinet.py','role':'Authored explanations of UV-Net and AutoMate. No model inference or CAD kernel execution.','uvnet':'The full canonical handle is shown as input and with two possible output types. Handle, grip surface, and support surface are hypothetical training labels authored for teaching, not predictions from the published model. Colors identify surface regions; rendering uses the shared primitive geometry rather than a CAD-kernel boolean union.','automate':'The handle is moved outward only for illustration. Gold marks mounting regions. The fixed mate is an authored example of a user choice, not a model prediction. The face-edge-vertex sketch omits loops for clarity.','sources':['https://arxiv.org/html/2006.10211v2','https://arxiv.org/html/2105.12238v2']},indent=2)+'\n')
 print('Generated UV-Net and AutoMate plates; canonical mounting alignment verified.')
if __name__=='__main__':main()
