#!/usr/bin/env python3
"""Canonical teaching cabinet: deterministic geometry shared by book figures.

Coordinates (metres): X right, -Y front, Z up. ``drawer`` is its opening in
metres along -Y; ``door`` is the outward opening angle in DEGREES. The body is
fixed. Handles are rigid pieces of their owners, so the cabinet has two DOF.

``BOX_PARTS`` and ``CYLINDER_PARTS`` describe the closed pose. ``mesh(n=32,
drawer=0, door=0)`` returns aligned numpy arrays: triangles [T,3,3], colors
[T,3] in 0..255, groups [T], and names [T]. Every individual primitive has a
closed, outward-wound surface. Adjacent panels may share their boundary.

The five flush pieces of the drawer front retain the teaching file labels
original-34/36/37/35/40.obj. These labels preserve the five-files/one-part
lesson; this newly constructed cabinet is not the original dataset mesh.
"""
from dataclasses import dataclass
from typing import Optional
import math
import numpy as np

TEAL = (108, 153, 150)
BLUE = (91, 141, 184)
GOLD = (219, 181, 85)
SILVER = (207, 216, 215)
HANDLE_GOLD = (177, 136, 47)
HINGE = np.array([-.51, -.46, 0.])
DRAWER_LIMIT = .76
DOOR_LIMIT = 90.


def _box(name, lo, hi, color, group='body', original_file=None):
    result = dict(kind='box', name=name, lo=lo, hi=hi, color=color, group=group)
    if original_file:
        result['original_file'] = original_file
    return result


BOX_PARTS = [
    _box('body-left-wall', (-.62,-.43,-.86), (-.54,.43,.86), TEAL),
    _box('body-right-wall', (.54,-.43,-.86), (.62,.43,.86), TEAL),
    _box('body-back', (-.54,.35,-.86), (.54,.43,.86), TEAL),
    _box('body-bottom', (-.54,-.43,-.86), (.54,.35,-.78), TEAL),
    _box('body-top', (-.54,-.43,.78), (.54,.35,.86), TEAL),
    _box('body-divider-shelf', (-.54,-.43,.28), (.54,.35,.32), TEAL),
    _box('body-left-frame', (-.54,-.445,-.78), (-.515,-.40,.78), TEAL),
    _box('body-right-frame', (.515,-.445,-.78), (.54,-.40,.78), TEAL),
    _box('body-lower-frame', (-.515,-.445,-.78), (.515,-.40,-.735), TEAL),
    _box('body-upper-frame', (-.515,-.445,.745), (.515,-.40,.78), TEAL),
    _box('body-middle-frame', (-.515,-.445,.265), (.515,-.40,.325), TEAL),
    _box('drawer-front-top-rail', (-.43,-.49,.68), (.43,-.43,.74), BLUE, 'drawer', 'original-34.obj'),
    _box('drawer-front-bottom-rail', (-.43,-.49,.33), (.43,-.43,.39), BLUE, 'drawer', 'original-36.obj'),
    _box('drawer-front-left-stile', (-.51,-.49,.33), (-.43,-.43,.74), BLUE, 'drawer', 'original-37.obj'),
    _box('drawer-front-right-stile', (.43,-.49,.33), (.51,-.43,.74), BLUE, 'drawer', 'original-35.obj'),
    _box('drawer-front-center', (-.43,-.49,.39), (.43,-.43,.68), BLUE, 'drawer', 'original-40.obj'),
    _box('drawer-floor', (-.49,-.43,.35), (.49,.30,.39), BLUE, 'drawer'),
    _box('drawer-left-wall', (-.49,-.43,.39), (-.455,.30,.70), BLUE, 'drawer'),
    _box('drawer-right-wall', (.455,-.43,.39), (.49,.30,.70), BLUE, 'drawer'),
    _box('drawer-back', (-.455,.265,.39), (.455,.30,.70), BLUE, 'drawer'),
    _box('door-panel', (-.51,-.49,-.73), (.51,-.43,.26), GOLD, 'door'),
]


def _cylinder(name, start, end, radius, color, group):
    return dict(kind='cylinder', name=name, start=start, end=end,
                radius=radius, color=color, group=group)


CYLINDER_PARTS = [
    _cylinder('drawer-handle-grip', (-.25,-.65,.53), (.25,-.65,.53), .05, SILVER, 'drawer'),
    _cylinder('drawer-handle-left-support', (-.21,-.49,.53), (-.21,-.65,.53), .036, SILVER, 'drawer'),
    _cylinder('drawer-handle-right-support', (.21,-.49,.53), (.21,-.65,.53), .036, SILVER, 'drawer'),
    _cylinder('door-handle-grip', (.36,-.64,-.35), (.36,-.64,-.10), .045, HANDLE_GOLD, 'door'),
    _cylinder('door-handle-lower-support', (.36,-.49,-.31), (.36,-.64,-.31), .032, HANDLE_GOLD, 'door'),
    _cylinder('door-handle-upper-support', (.36,-.49,-.14), (.36,-.64,-.14), .032, HANDLE_GOLD, 'door'),
]
PARTS = BOX_PARTS + CYLINDER_PARTS
PART_BY_NAME = {part['name']: part for part in PARTS}


def pose_transform(group, drawer=0., door=0.):
    """Return R,t for p_world = p_closed @ R.T + t (door is degrees)."""
    r = np.eye(3)
    t = np.zeros(3)
    if group == 'drawer':
        t[1] = -float(drawer)
    elif group == 'door':
        angle = math.radians(-door)
        c, s = math.cos(angle), math.sin(angle)
        r = np.array([[c,-s,0.], [s,c,0.], [0.,0.,1.]])
        t = HINGE - r @ HINGE
    return r, t


def _cylinder_basis(part):
    start, end = np.asarray(part['start']), np.asarray(part['end'])
    length = np.linalg.norm(end-start)
    axis = (end-start)/length
    ref = np.array([0.,0.,1.]) if abs(axis[2]) < .9 else np.array([1.,0.,0.])
    u = np.cross(axis,ref)
    u /= np.linalg.norm(u)
    return start, end, axis, u, np.cross(axis,u), length


def part_triangles(part, n=32):
    """Triangles for one closed-pose primitive, with outward winding."""
    if part['kind'] == 'box':
        lo, hi = np.array(part['lo']), np.array(part['hi'])
        center = (lo+hi)/2
        vs = np.array([[x,y,z] for x in (lo[0],hi[0])
                       for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
        result = []
        for indices in [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(1,5,7,3),(0,2,6,4)]:
            face = vs[list(indices)]
            if np.cross(face[1]-face[0],face[2]-face[0]) @ (face.mean(axis=0)-center) < 0:
                face = face[::-1]
            result.extend([face[[0,1,2]], face[[0,2,3]]])
        return np.array(result)
    if n < 3:
        raise ValueError('A cylinder needs at least three radial sides.')
    start, end, axis, u, v, length = _cylinder_basis(part)
    ring = np.array([part['radius']*(u*math.cos(2*math.pi*i/n)+v*math.sin(2*math.pi*i/n)) for i in range(n)])
    a, b = start+ring, end+ring
    result = []
    for i in range(n):
        j = (i+1) % n
        result.extend([(a[i],a[j],b[j]), (a[i],b[j],b[i]),
                       (start,a[j],a[i]), (end,b[i],b[j])])
    return np.array(result)


@dataclass
class CabinetMesh:
    triangles: np.ndarray
    colors: np.ndarray
    groups: np.ndarray
    names: np.ndarray


def mesh(n=32, drawer=0., door=0., groups=None):
    """Build a posed, opaque triangle mesh. ``groups`` optionally selects parts."""
    triangles, colors, part_groups, names = [], [], [], []
    for part in PARTS:
        if groups is not None and part['group'] not in groups:
            continue
        ts = part_triangles(part,n)
        r,t = pose_transform(part['group'],drawer,door)
        triangles.extend(ts @ r.T + t)
        colors.extend([part['color']]*len(ts))
        part_groups.extend([part['group']]*len(ts))
        names.extend([part['name']]*len(ts))
    return CabinetMesh(np.array(triangles), np.array(colors), np.array(part_groups), np.array(names))


def field(points, drawer=0., door=0., density=80., edge=.008):
    """Analytic teaching field, NOT a trained NeRF.

    Return (sigma, rgb): sigma [N] and RGB [N,3] in 0..1. Box and finite
    cylinder signed distances provide a thin smooth boundary; interiors are
    dense. Queries accept arbitrary leading dimensions [...,3].
    """
    points = np.asarray(points,float)
    shape = points.shape[:-1]
    flat = points.reshape(-1,3)
    best = np.full(len(flat),np.inf)
    rgb = np.zeros((len(flat),3))
    for part in PARTS:
        r,t = pose_transform(part['group'],drawer,door)
        p = (flat-t) @ r
        if part['kind'] == 'box':
            lo,hi = np.array(part['lo']),np.array(part['hi'])
            q = np.abs(p-(lo+hi)/2) - (hi-lo)/2
            sd = np.linalg.norm(np.maximum(q,0),axis=1) + np.minimum(q.max(axis=1),0)
        else:
            start,end,axis,u,v,length = _cylinder_basis(part)
            q = p-(start+end)/2
            axial = q @ axis
            radial = np.linalg.norm(q-axial[:,None]*axis,axis=1)
            d = np.column_stack((radial-part['radius'],np.abs(axial)-length/2))
            sd = np.linalg.norm(np.maximum(d,0),axis=1) + np.minimum(d.max(axis=1),0)
        mask = sd < best
        best[mask] = sd[mask]
        rgb[mask] = np.asarray(part['color'])/255.
    sigma = density/(1+np.exp(np.clip(best/max(edge,1e-9),-60,60)))
    return sigma.reshape(shape), rgb.reshape(shape+(3,))


@dataclass
class GaussianSamples:
    centers: np.ndarray
    covariances: np.ndarray
    colors: np.ndarray
    opacities: np.ndarray
    groups: np.ndarray
    names: np.ndarray
    normals: np.ndarray


def gaussians(spacing=.075, drawer=0., door=0., opacity=.72):
    """Surface Gaussian samples of the SAME primitives (not fitted 3DGS).

    Returned colors are in 0..1; covariances are in metres squared. Each
    surface mark is broad tangent to the surface and thin along its normal.
    All marks belong to the same group/name as the mesh surface they sample.
    """
    centers,covs,colors,opacities,groups,names,normals = [],[],[],[],[],[],[]
    def emit(p, normal, part, sigma, covariance=None):
        r,t = pose_transform(part['group'],drawer,door)
        p = np.asarray(p) @ r.T + t
        normal = r @ normal
        cov = (np.eye(3)*sigma**2 + np.outer(normal,normal)*((sigma*.15)**2-sigma**2)
               if covariance is None else r @ covariance @ r.T)
        centers.append(p); covs.append(cov); colors.append(np.asarray(part['color'])/255.)
        opacities.append(opacity); groups.append(part['group']); names.append(part['name'])
        normals.append(normal)
    for part in PARTS:
        if part['kind'] == 'box':
            lo,hi=np.asarray(part['lo']),np.asarray(part['hi'])
            for axis in range(3):
                axes=[d for d in range(3) if d!=axis]
                grids=[]; sigmas=np.full(3,.006)
                for d in axes:
                    count=max(1,int(np.ceil((hi[d]-lo[d])/spacing)))
                    grids.append(lo[d]+(np.arange(count)+.5)*(hi[d]-lo[d])/count)
                    sigmas[d]=(hi[d]-lo[d])/count*.62
                for sign in (-1,1):
                    normal=np.eye(3)[axis]*sign
                    for a in grids[0]:
                        for b in grids[1]:
                            p=np.zeros(3); p[axis]=lo[axis] if sign<0 else hi[axis]
                            p[axes]=[a,b]
                            emit(p,normal,part,spacing*.58,np.diag(sigmas**2))
        else:
            start,end,axis,u,v,length=_cylinder_basis(part)
            radius=part['radius']
            count=max(12,int(np.ceil(2*np.pi*radius/spacing)))
            along=max(2,int(np.ceil(length/min(spacing,radius*.8))))
            for j in range(along):
                center=start+(end-start)*(j+.5)/along
                for i in range(count):
                    normal=u*math.cos(2*np.pi*i/count)+v*math.sin(2*np.pi*i/count)
                    emit(center+radius*normal,normal,part,min(spacing*.58,radius*.6))
            for center,normal in ((start,-axis),(end,axis)):
                emit(center,normal,part,radius*.6)
                for i in range(count):
                    direction=u*math.cos(2*np.pi*i/count)+v*math.sin(2*np.pi*i/count)
                    emit(center+radius*.65*direction,normal,part,radius*.45)
    return GaussianSamples(*(np.array(a) for a in (centers,covs,colors,opacities,groups,names,normals)))


def validate(n=32):
    """Verify non-degenerate, closed, outward-oriented individual primitives."""
    for part in PARTS:
        tris=part_triangles(part,n)
        assert np.all(np.linalg.norm(np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]),axis=1)>1e-10),part['name']
        edges={}
        for tri in tris:
            for a,b in zip(tri,np.roll(tri,-1,axis=0)):
                aa,bb=tuple(np.round(a,10)),tuple(np.round(b,10))
                key=tuple(sorted((aa,bb)))
                edges.setdefault(key,[]).append(1 if aa<bb else -1)
        assert all(len(v)==2 and sum(v)==0 for v in edges.values()),part['name']
        volume=np.sum(np.einsum('ij,ij->i',tris[:,0],np.cross(tris[:,1],tris[:,2])))/6
        assert volume>0,part['name']
    return {'boxes':len(BOX_PARTS),'cylinders':len(CYLINDER_PARTS),
            'triangles':len(mesh(n).triangles),'radial_sides':n,'dof':2}


if __name__ == '__main__':
    for n in (6,32):
        print(validate(n))
