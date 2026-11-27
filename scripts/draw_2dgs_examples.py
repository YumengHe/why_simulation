#!/usr/bin/env python3
"""Compare volumetric and planar Gaussians using the canonical cabinet.

Authored teaching elements, not trained 3DGS/2DGS results. Ellipsoid and disk
guides are two-sigma contours. Cabinet disks are evaluated by ray/plane
intersection; volumetric marks use a projected covariance. The pale mesh is
context only. No reconstruction or mesh extraction is claimed.
"""
from pathlib import Path
from html import escape
import json
import numpy as np
from PIL import Image, ImageDraw
from draw_dust3r_examples import raster, camera, FOCAL, PAPER, label, INK, MUTED, BLUE, CORAL, GOLD

OUT = Path(__file__).resolve().parents[1] / 'book/assets/2dgs'
W, H = 600, 700
EYE = np.array([2.8, -6., 2.5]); EYE /= np.linalg.norm(EYE)
RIGHT = np.cross([0., 0., 1.], EYE); RIGHT /= np.linalg.norm(RIGHT)
UP = np.cross(EYE, RIGHT)
SCREEN = np.array([RIGHT, -UP])


def polyline(d, p, color, width=2):
    d.line([tuple(x) for x in p], fill=color, width=width)


def arrow(d, a, b, color, width=3):
    a, b = np.array(a), np.array(b)
    direction = (b-a)/np.linalg.norm(b-a)
    side = np.array([-direction[1], direction[0]])
    polyline(d, [a, b], color, width)
    d.polygon([tuple(b), tuple(b-11*direction+5*side), tuple(b-11*direction-5*side)], fill=color)


def soft_mark(rgb, center, covariance, color, opacity=.65):
    yy, xx = np.mgrid[:rgb.shape[0], :rgb.shape[1]]
    delta = np.stack([xx+.5-center[0], yy+.5-center[1]], axis=-1)
    q = np.einsum('...i,ij,...j->...', delta, np.linalg.inv(covariance), delta)
    alpha = opacity*np.exp(-q/2)
    return rgb*(1-alpha[..., None])+np.array(color)*alpha[..., None]


def element_figure(planar):
    rgb = np.full((H, W, 3), PAPER, dtype=float)
    sizes = np.array([.66, 0. if planar else .28, .48])
    cov = np.diag(sizes**2)
    assert np.linalg.matrix_rank(cov) == (2 if planar else 3)
    scale, center = 125., np.array([300., 265.])
    rgb = soft_mark(rgb, center, scale**2*SCREEN@cov@SCREEN.T, [91, 141, 184])
    im = Image.fromarray(np.uint8(rgb)); d = ImageDraw.Draw(im)
    theta = np.linspace(0, 2*np.pi, 180)
    pairs = [(0, 2)] if planar else [(0, 1), (0, 2), (1, 2)]
    for a, b in pairs:
        ring = np.zeros((len(theta), 3))
        ring[:, a] = 2*sizes[a]*np.cos(theta)
        ring[:, b] = 2*sizes[b]*np.sin(theta)
        polyline(d, ring@SCREEN.T*scale+center, BLUE, 3)
    for axis, index, color in [(0, '1', BLUE), (2, '2', BLUE)]+([] if planar else [(1, '3', CORAL)]):
        endpoint = np.eye(3)[axis]*sizes[axis]*2.5
        if axis == 1: endpoint *= -1
        p = endpoint@SCREEN.T*scale+center
        arrow(d, center, p, color)
        offset = (p-center)/np.linalg.norm(p-center)*19
        label(d, p+offset, index, 28, color, True)
    d.ellipse((295, 260, 305, 270), fill=GOLD)
    label(d, (300, 35), '2DGS: one planar Gaussian' if planar else '3DGS: one 3D Gaussian', 30, bold=True)
    label(d, (300, 79), 'An oriented, soft disk' if planar else 'A soft ellipsoid', 26, MUTED)
    label(d, (300, 415), '1: width     2: height' if planar else '1: width   2: height   3: thickness', 25, MUTED)
    d.line((35, 449, 565, 449), fill='#dedfd7', width=2)
    label(d, (300, 480), 'The same element, seen edge-on', 25, bold=True)
    if planar:
        # A one-pixel mathematical line is drawn thicker solely for readability.
        for y in range(508, 633):
            strength = np.exp(-.5*((y-570)/31)**2)
            col = tuple(np.uint8(np.array(PAPER)*(1-strength)+np.array([91, 141, 184])*strength))
            d.line((298, y, 302, y), fill=col)
        label(d, (300, 665), 'Zero thickness through the disk', 25, MUTED)
    else:
        a = np.asarray(im, dtype=float).copy()
        # The same Y/Z scales, viewed from X, at a smaller display magnification.
        half_width, half_height = 2*sizes[1]*65, 2*sizes[2]*65
        a = soft_mark(a, [300, 570], np.diag([(half_width/2)**2, (half_height/2)**2]), [91, 141, 184], .7)
        im = Image.fromarray(np.uint8(a)); d = ImageDraw.Draw(im)
        d.ellipse((300-half_width, 570-half_height, 300+half_width, 570+half_height), outline=BLUE, width=2)
        arrow(d, [300, 570], [300+half_width, 570], CORAL)
        label(d, (300, 665), 'A third size gives thickness', 25, MUTED)
    return im


def elements():
    result = []
    def emit(p, u, v, color):
        u, v = np.array(u, float), np.array(v, float)
        n = np.cross(u, v)
        assert abs(n@u)<1e-12 and abs(n@v)<1e-12
        result.append((np.array(p), u, v, n, np.array(color)))
    # Selected visible patches; all other cabinet parts remain visible as context.
    for x in [-.36, 0., .36]:
        for z in [.37, .69]: emit([x, -.495, z], [1,0,0], [0,0,1], [91,141,184])
    for x in [-.36, -.09, .18]:
        for z in [-.60, -.24, .12]: emit([x, -.495, z], [1,0,0], [0,0,1], [219,181,85])
    for x in [-.36, 0., .36]:
        for y in [-.20, .14]: emit([x, y, .866], [1,0,0], [0,1,0], [108,153,150])
    for y in [-.25, .12]:
        for z in [-.65, -.15, .35, .70]: emit([.626, y, z], [0,1,0], [0,0,1], [108,153,150])
    return result


def cabinet_figure(planar):
    image, points, _ = raster(28)
    rgb = .28*np.asarray(image, float)+.72*np.array(PAPER)
    origin, basis = camera(28)
    yy, xx = np.mgrid[:600, :600]
    rays = np.stack([(xx+.5-300)/FOCAL, (yy+.5-300)/FOCAL, np.ones_like(xx)], axis=-1)@basis
    tangent_sigma, normal_sigma = .045, .026
    guides = []
    theta = np.linspace(0, 2*np.pi, 100)
    def project(p):
        cam = (p-origin)@basis.T
        return FOCAL*cam[..., :2]/cam[..., 2, None]+300
    patches = elements()
    # Draw back-to-front, using exactly the same centers for both diagrams.
    patches.sort(key=lambda p: np.linalg.norm(p[0]-origin), reverse=True)
    for center, u, v, n, color in patches:
        assert abs(u@v)<1e-12
        if planar:
            den = rays@n
            t = ((center-origin)@n)/np.where(abs(den)>1e-9, den, 1)
            delta = origin+rays*t[..., None]-center
            assert np.max(abs(delta[abs(den)>1e-9]@n))<1e-10
            q = ((delta@u)/tangent_sigma)**2+((delta@v)/tangent_sigma)**2
            alpha = .75*np.exp(-q/2)*(t>0)*(abs(den)>1e-9)
            # Respect closer geometry, e.g. the handle in front of the panel.
            surface_depth = ((points-origin)@basis.T)[..., 2]
            alpha *= np.isfinite(surface_depth)&(t<=surface_depth+.025)
            rgb = rgb*(1-alpha[..., None])+color*alpha[..., None]
        else:
            covariance = tangent_sigma**2*(np.outer(u,u)+np.outer(v,v))+normal_sigma**2*np.outer(n,n)
            x, y, z = (center-origin)@basis.T
            jac = np.array([[FOCAL/z,0,-FOCAL*x/z**2],[0,FOCAL/z,-FOCAL*y/z**2]])@basis
            rgb = soft_mark(rgb, project(center), jac@covariance@jac.T, color, .75)
        pairs = [(u, v, tangent_sigma, tangent_sigma)]
        if not planar: pairs += [(u,n,tangent_sigma,normal_sigma),(v,n,tangent_sigma,normal_sigma)]
        for a,b,sa,sb in pairs:
            ring = center+2*sa*np.cos(theta)[:,None]*a+2*sb*np.sin(theta)[:,None]*b
            if planar: assert np.max(abs((ring-center)@n))<1e-12
            guides.append((project(ring), tuple(np.uint8(color*.68))))
    im = Image.new('RGB', (600, 700), PAPER)
    im.paste(Image.fromarray(np.uint8(np.clip(rgb,0,255))), (0, 65))
    d = ImageDraw.Draw(im)
    for ring, color in guides: polyline(d, ring+[0,65], color, 1)
    label(d, (300, 34), '2DGS: disks along the surfaces' if planar else '3DGS: ellipsoids near surfaces', 29, bold=True)
    label(d, (300, 655), f'{len(patches)} selected element guides', 25, MUTED)
    label(d, (300, 686), 'Same cabinet, centers, and camera', 24, MUTED)
    return im


def workflow():
    # The two columns are separate fits, with aligned steps. The optional mesh
    # arrow starts from the saved 2DGS representation, not the rendered image.
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1240" viewBox="0 0 1000 1240" role="img" aria-labelledby="title desc">',
           '<title id="title">Shared inputs, two Gaussian reconstruction routes</title>',
           '<desc id="desc">Cabinet photographs, cameras and sparse points branch into 3DGS and 2DGS. Each route initializes elements, repeatedly renders and adjusts them, saves its own representation, and renders new camera views. 2DGS adds surface constraints; its saved disks can also supply depth maps for mesh extraction.</desc>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 1L9 5L0 9" fill="none" stroke="#64736c" stroke-width="1.6"/></marker><marker id="gold-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 1L9 5L0 9" fill="none" stroke="#9b772b" stroke-width="1.6"/></marker></defs>',
           '<rect width="1000" height="1240" fill="#fefdfb"/>']
    def text(x,y,value,size=24,bold=False,color='#293632'):
        parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{600 if bold else 400}" fill="{color}">{escape(value)}</text>')
    def box(x,y,w,h,fill='#f3f7f5',stroke='#d3ddd8'):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    def path(value,gold=False,dashed=False):
        color='#9b772b' if gold else '#64736c'
        marker='gold-arrow' if gold else 'arrow'
        dash=' stroke-dasharray="6 5"' if dashed else ''
        parts.append(f'<path d="{value}" fill="none" stroke="{color}" stroke-width="2"{dash} marker-end="url(#{marker})"/>')
    text(500,43,'One set of cabinet photographs, two routes',30,True)
    text(500,77,'Choose a route; each column fits its own 3D representation.',23)
    box(130,105,740,92)
    text(500,140,'1 · Prepare the inputs',26,True)
    text(500,176,'Photographs + cameras + sparse 3D points (Section 2.8)',23)
    path('M500 197V216H270V247')
    path('M500 216H730V247')
    text(270,278,'3DGS',31,True)
    text(730,278,'2DGS',31,True)

    for cx, planar in [(270,False),(730,True)]:
        x=cx-200
        box(x,304,400,94,'#fcf4e2','#cfb674')
        text(cx,340,'2 · Initialize the elements',25,True)
        text(cx,375,'Flat disks placed in 3D' if planar else 'Soft ellipsoids with thickness',23)
        path(f'M{cx} 398V428')

        box(x,435,400,316,'#fefdfb')
        text(cx,470,'3 · Render, compare, adjust',25,True)
        box(x+35,489,330,76)
        text(cx,520,'Use the 2DGS renderer' if planar else 'Use the 3DGS renderer',23,True)
        text(cx,549,'Render a photographed view',22)
        path(f'M{cx} 565V590')
        box(x+35,597,330,105,'#fcf4e2' if planar else '#f3f7f5',
            '#cfb674' if planar else '#d3ddd8')
        text(cx,627,'Compare with the photograph',21,True)
        if planar:
            text(cx,656,'Adjust using image differences',21)
            text(cx,684,'+ surface constraints',22,True,'#82621c')
        else:
            text(cx,656,'Adjust using',22)
            text(cx,684,'image differences',22)
        # Return to rendering after an update; exit downward once fitting ends.
        path(f'M{x+35} 650H{x+16}V527H{x+35}')
        text(cx,732,'Repeat across the camera views',21)
        path(f'M{cx} 751V785')

        box(x,792,400,83)
        text(cx,824,'4 · Save the fitted representation',22,True)
        text(cx,855,'Disks and their parameters' if planar else 'Ellipsoids and their parameters',23)
        path(f'M{cx} 875V920')
        box(x,927,400,101)
        text(cx,960,'5 · Use: render another view',24,True)
        text(cx,990,'New camera + corresponding renderer',21)
        text(cx,1016,'→ a new 2D color image',22)

    # Separate path: the saved disks render depth, which is fused into a mesh.
    path('M930 834H972V1127H930',gold=True,dashed=True)
    box(530,1070,400,127,'#fcf4e2','#cfb674')
    text(730,1102,'Optional: extract a mesh',25,True)
    text(730,1133,'Saved disks → render depth maps',22)
    text(730,1163,'Combine depth → extract surfaces',22)

    box(70,1084,20,20)
    text(282,1101,'Shared operation',23)
    box(70,1122,20,20,'#fcf4e2','#cfb674')
    text(282,1139,'Method-specific detail',23)
    text(270,1180,'A 3DGS mesh uses an additional',20)
    text(270,1207,'surface-reconstruction workflow.',20)
    text(730,1225,'Surface constraints guide depth and facing direction.',18)
    (OUT/'workflow.svg').write_text('\n'.join(parts+['</svg>'])+'\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for planar, name in [(False,'3d'),(True,'2d')]:
        element_figure(planar).save(OUT/f'element-{name}.png')
        cabinet_figure(planar).save(OUT/f'cabinet-{name}.png')
    workflow()
    (OUT/'manifest.json').write_text(json.dumps({
        'generator':'scripts/draw_2dgs_examples.py',
        'geometry':'scripts/shared_cabinet.py',
        'rasterizer':'scripts/draw_dust3r_examples.py',
        'provenance':'Authored explanatory diagrams; neither trained outputs nor a comparative quality test.',
        'cabinet_guides':len(elements()),
        'dimensions':'3D elements have positive variance on three axes; 2D elements have two in-plane variances and zero normal variance.',
        'guide_contours':'Two standard deviations, not hard support boundaries. Edge-on line width is a display aid.',
        'disk_rendering':'Ray/plane intersection, in-plane Gaussian evaluation, and a context-mesh visibility mask.',
        'volume_rendering':'Local projected covariance for soft marks; illustrative ellipsoid guides.',
        'checks':'Covariance rank, orthogonal axes, and planar ray intersections are asserted.',
        'mesh':'The pale cabinet is the shared authored mesh; no extraction was performed.',
        'workflow':'Shared inputs split into aligned 3DGS and 2DGS routes. Each has its own fitting loop and saved representation. Optional mesh extraction branches from saved 2DGS disks via depth rendering and fusion.',
        'sources':['https://surfsplatting.github.io/','https://arxiv.org/abs/2403.17888','https://github.com/hbb1/2d-gaussian-splatting'],
    },indent=2)+'\n')
    print(f'Created 5 Gaussian comparison diagrams, with {len(elements())} shared cabinet element centers.')


if __name__=='__main__': main()
