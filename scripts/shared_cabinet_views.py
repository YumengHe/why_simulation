"""Small deterministic vector views of the canonical cabinet and its parts."""
import numpy as np
from shared_cabinet import mesh

def vector(model=None,size=(340,320),eye=(3,-6,2.6),center=(0,-.2,0),scale=130,xy=None,wire=False,omit=(),color_override=None,opacity=1):
    model=mesh() if model is None else model
    eye=np.array(eye,float);eye/=np.linalg.norm(eye)
    right=np.cross([0,0,1],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
    xy=np.array(xy if xy else (size[0]/2,size[1]/2))
    light=np.array([-3.,-5.,7.]);light/=np.linalg.norm(light)
    faces=[]
    for tri,col,name in zip(model.triangles,model.colors,model.names):
        if name in omit:continue
        normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal)
        if normal@eye<=1e-9:continue
        shade=.65+.35*max(0,normal@light)
        if color_override is not None:col=color_override(name,col)
        rgb=np.array(col)*shade;fill='#'+''.join(f'{round(c):02x}' for c in rgb)
        points=(tri-np.asarray(center))@np.array([right,-up]).T*scale+xy
        pts=' '.join(f'{x:.2f},{y:.2f}' for x,y in points)
        edge='#405752' if wire else fill
        faces.append((tri.mean(0)@eye,f'<polygon points="{pts}" fill="{fill}" stroke="{edge}" stroke-width="{.5 if wire else .25}" stroke-linejoin="round"/>'))
    return f'<g opacity="{opacity}">'+''.join(v for _,v in sorted(faces,key=lambda t:t[0]))+'</g>'

def side(drawer=0,scale=120,xy=(140,230)):
    return vector(mesh(n=12,drawer=drawer),eye=(-1,0,0),center=(0,0,0),scale=scale,xy=xy,omit=('body-left-wall','body-left-frame','drawer-left-wall'))
