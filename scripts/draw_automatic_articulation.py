#!/usr/bin/env python3
"""Illustrate articulation pipelines with the canonical scripted cabinet.

No inference is run. Part ownership, boxes and poses are authored examples.
Opaque depth-tested renders use shared_cabinet.py; annotation uses Pillow.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from shared_cabinet import mesh, CabinetMesh, validate, TEAL, BLUE, GOLD, pose_transform
from preview_shared_cabinet import render, font

OUT = Path(__file__).resolve().parents[1] / 'book/assets/automatic-articulation'
PAPER = (254, 253, 251)
INK, MUTED, LINE = '#293632', '#5f6862', '#d9ddd8'
CBLUE, CGOLD, CTEAL = '#39759e', '#997018', '#467e79'
MODEL, PROGRAM = '#805095', '#946b35'
EYE = (3., -6., 2.6)
CENTRE = (0., -.2, 0.)
SCALE = 157


def text(draw, xy, lines, size=25, color=INK, bold=False, anchor='la'):
    if isinstance(lines, str):
        lines = [lines]
    for i, line in enumerate(lines):
        draw.text((xy[0], xy[1] + i * (size + 9)), line,
                  font=font(size, bold), fill=color, anchor=anchor)


def arrow(draw, start, end, color=MUTED, width=3):
    a, b = np.array(start, float), np.array(end, float)
    u = (b-a)/np.linalg.norm(b-a)
    v = np.array([-u[1], u[0]])
    draw.line([tuple(a), tuple(b)], fill=color, width=width)
    draw.polygon([tuple(b), tuple(b-12*u+5*v), tuple(b-12*u-5*v)], fill=color)


def cabinet(mode='appearance', drawer=0., door=0., groups=None):
    model = mesh(n=32, drawer=drawer, door=door, groups=groups)
    if mode == 'gray':
        model = CabinetMesh(model.triangles, np.full_like(model.colors, 194), model.groups, model.names)
    elif mode == 'parts':
        palette = {'body': TEAL, 'drawer': BLUE, 'door': GOLD}
        model = CabinetMesh(model.triangles, np.array([palette[g] for g in model.groups]), model.groups, model.names)
    return render(model, size=(360, 385), eye=EYE, center=CENTRE,
                  scale=SCALE, ss=3, edges=mode == 'gray')


def base(title, subtitle):
    im = Image.new('RGB', (1200, 720), PAPER)
    d = ImageDraw.Draw(im)
    text(d, (30, 26), title, 33, bold=True)
    text(d, (30, 76), subtitle, 24, MUTED)
    for x in (405, 795):
        d.line((x, 130, x, 643), fill=LINE, width=2)
    text(d, (30, 676), 'Scripted cabinet illustration · stages explain the method, not measured predictions.', 21, MUTED)
    return im, d


def project(points, size=(360, 385), scale=SCALE, center=CENTRE):
    eye = np.array(EYE, float); eye /= np.linalg.norm(eye)
    right = np.cross([0., 0., 1.], eye); right /= np.linalg.norm(right)
    up = np.cross(eye, right)
    p = np.asarray(points)-np.array(center)
    return np.column_stack((size[0]/2 + scale*(p @ right), size[1]/2 - scale*(p @ up)))


def anymesh():
    im, d = base('Articulate AnyMesh: start with an existing mesh',
                 'The cabinet already has a 3D shape. The method adds its movement structure.')
    titles = [('1  Input', 'Cabinet surface mesh'), ('2  Process', 'VLM judgments + geometry'), ('3  Output', 'Articulated parts and joints')]
    for x, (h, sub) in zip((30, 420, 810), titles):
        text(d, (x, 132), h, 28, bold=True)
        text(d, (x, 173), sub, 23, MUTED)
    im.paste(cabinet('gray'), (30, 211))
    im.paste(cabinet('parts'), (420, 211))
    im.paste(cabinet(drawer=.40, door=52), (810, 211))
    d = ImageDraw.Draw(im)
    for x in (389, 779):
        arrow(d, (x, 369), (x+29, 369))
    text(d, (30, 592), ['One object’s surfaces', 'before adding movement'], 23)
    for x, label, color in [(425, 'Body', CTEAL), (535, 'Drawer', CBLUE), (675, 'Door', CGOLD)]:
        d.ellipse((x, 600, x+14, 614), fill=color)
        text(d, (x+23, 594), label, 22, color)
    text(d, (420, 626), 'Handles belong to their moving parts.', 20, MUTED)
    text(d, (810, 592), ['Drawer slides; door rotates.', 'Geometry and texture are also refined.'], 21)
    im.save(OUT/'anymesh-cabinet.png')
    mobile_stages(im, 'anymesh-cabinet-mobile.png', 'Articulate AnyMesh',
                  ['Start with an existing mesh.', 'Add parts and joints.'])


def urdformer():
    im, d = base('URDFormer: start with an image and part boxes',
                 'Predict a structure, then assemble it with prepared part meshes and a URDF template.')
    for x, h, sub in [(30, '1  Input', 'Image + detected part boxes'),
                       (420, '2  Process', 'Network predictions + rules'),
                       (810, '3  Output', 'URDF + selected part meshes')]:
        text(d, (x, 132), h, 28, bold=True)
        text(d, (x, 173), sub, 23, MUTED)
    im.paste(cabinet(), (30, 211))
    im.paste(cabinet(drawer=.40, door=52), (810, 211))
    d = ImageDraw.Draw(im)
    m = mesh(n=32)
    boxes = {}
    selections = [('drawer', (m.groups == 'drawer') & np.char.startswith(m.names, 'drawer-front'), CBLUE),
                  ('door', m.names == 'door-panel', CGOLD),
                  ('handle', np.char.startswith(m.names, 'drawer-handle'), '#8b488c')]
    for name, select, color in selections:
        p = project(m.triangles[select].reshape(-1, 3))
        lo, hi = p.min(axis=0)+[30,211]-4, p.max(axis=0)+[30,211]+4
        assert np.all(hi > lo)
        d.rectangle((*lo, *hi), outline=color, width=3)
        boxes[name] = [lo.tolist(), hi.tolist()]
    text(d, (30, 592), ['Rectangles locate visible parts', 'in the 2D picture.'], 22)
    d.rounded_rectangle((430, 244, 778, 468), radius=8, fill='white', outline=LINE, width=2)
    text(d, (447, 262), 'Example: the drawer', 24, CBLUE, True)
    for y, label, value in [(313, 'Mesh type', 'Drawer'), (348, 'Position', 'Upper body'),
                            (383, 'Size', 'Fit to image'), (418, 'Parent', 'Cabinet body')]:
        text(d, (447, y), label, 21, MUTED)
        text(d, (588, y), value, 21)
    arrow(d, (600, 477), (600, 504))
    text(d, (600, 518), ['Program assigns joints', 'using part-category rules'], 23, PROGRAM, True, anchor='ma')
    text(d, (420, 606), 'Place meshes and write the URDF.', 22)
    text(d, (810, 592), ['A proposed 3D arrangement', 'with parts that can move'], 23)
    for x in (389, 779):
        arrow(d, (x, 369), (x+29, 369))
    im.save(OUT/'urdformer-cabinet.png')
    mobile_stages(im, 'urdformer-cabinet-mobile.png', 'URDFormer',
                  ['Start with an image and part boxes.', 'Assemble an articulated model.'])
    return boxes


def mobile_stages(source, name, title, subtitle):
    im = Image.new('RGB', (420, 1870), PAPER)
    d = ImageDraw.Draw(im)
    text(d, (30, 22), title, 29, bold=True)
    text(d, (30, 69), subtitle, 22, MUTED)
    for i, x in enumerate((30, 420, 810)):
        y = 160 + i*550
        im.paste(source.crop((x, 130, x+360, 650)), (30,y))
        if i < 2:
            arrow(d, (210,y+520), (210,y+544))
    text(d, (30, 1828), 'Scripted teaching example', 20, MUTED)
    im.save(OUT/name)


def output_structure():
    im = Image.new('RGB', (1200, 650), PAPER)
    d = ImageDraw.Draw(im)
    text(d, (30, 26), 'Inspect the movement structure', 33, bold=True)
    text(d, (30, 76), 'For this cabinet: one fixed body, one sliding drawer, and one hinged door.', 25, MUTED)
    posed = mesh(n=32, drawer=.40, door=52)
    im.paste(render(posed, size=(500,450), eye=EYE, center=(0,-.2,0), scale=185, ss=3), (30,132))
    d = ImageDraw.Draw(im)
    d.line((565, 140, 565, 580), fill=LINE, width=2)
    def node(x, y, w, h, label, color):
        d.rounded_rectangle((x,y,x+w,y+h), radius=5, fill='white', outline=color, width=3)
        text(d, (x+w/2,y+17), label, 25,color,True,anchor='ma')
    node(805,155,170,66,'Body',CTEAL)
    d.line((890,221,890,255,715,255,715,320), fill=CBLUE, width=3)
    d.line((890,255,1065,255,1065,320), fill=CGOLD, width=3)
    d.rectangle((635,270,795,307),fill=PAPER)
    d.rectangle((990,270,1140,307),fill=PAPER)
    text(d,(715,272),'Sliding joint',23,CBLUE,anchor='ma')
    text(d,(1065,272),'Hinge joint',23,CGOLD,anchor='ma')
    node(615,323,200,66,'Drawer',CBLUE)
    node(965,323,200,66,'Door',CGOLD)
    text(d,(715,415),['Front, tray,','and fixed handle'],23,anchor='ma')
    text(d,(1065,415),['Panel and','fixed handle'],23,anchor='ma')
    text(d,(610,517),['URDF records the connections and joints.', 'Part mesh files supply the visible shapes.'],24)
    text(d,(30,601),'Scripted example of the structure to check · each method’s actual predictions can differ.',22,MUTED)
    im.save(OUT/'cabinet-output.png')


def joint_guides(method):
    """Compare model choices with explicit geometry calculations or templates.

    The plane, candidate points and predictions are authored on known cabinet
    geometry; they are not fitted from inference. Hinge points A/B are placed
    on its canonical vertical hinge line, and the normal is exactly -Y.
    """
    is_anymesh = method == 'anymesh'
    im = Image.new('RGB', (1200, 970), PAPER)
    d = ImageDraw.Draw(im)
    title = ('Articulate AnyMesh: choose a joint, then locate its axis' if is_anymesh
             else 'URDFormer: predict a category, then apply its joint rules')
    text(d, (30, 26), title, 31, bold=True)
    text(d, (30, 76), 'Purple: model predictions    Brown: ' +
         ('geometry calculations' if is_anymesh else 'preset assembly rules'), 24, MUTED)
    d.line((600, 130, 600, 910), fill=LINE, width=2)
    for part, x in [('drawer',30), ('door',630)]:
        text(d, (x,132), 'Drawer: sliding' if part == 'drawer' else 'Door: rotation',28,bold=True)
        d.rounded_rectangle((x,178,x+540,262), radius=5, fill='#f5f0f8', outline=MODEL,width=2)
        if is_anymesh:
            lines = (['GPT-4o proposes a sliding joint.', 'Movement: inward / outward.'] if part=='drawer'
                     else ['GPT-4o proposes a rotating joint.', 'Select hinge candidates A and B.'])
        else:
            lines = (['Network predicts the drawer category.', 'Position, size, and parent are also predicted.'] if part=='drawer'
                     else ['Network predicts the door category.', 'Example: a door hinged on the left.'])
        text(d,(x+16,189),lines,23,MODEL,True)
        settings = dict(size=(540,420),scale=178,center=(0,-.2,0))
        im.paste(render(mesh(n=32),eye=EYE,ss=3,**settings), (x,275))
        d = ImageDraw.Draw(im)
        def projected(points):
            return project(points,**settings)+[x,275]
        if part=='drawer':
            if is_anymesh:
                corners = np.array([[-.51,-.495,.33],[.51,-.495,.33],[.51,-.495,.74],[-.51,-.495,.74]])
                plane = projected(corners)
                overlay = Image.new('RGBA',im.size,(0,0,0,0))
                od = ImageDraw.Draw(overlay)
                od.polygon([tuple(p) for p in plane], fill=(57,117,158,48), outline=CBLUE, width=3)
                im = Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
                d = ImageDraw.Draw(im)
                normal = np.cross(corners[1]-corners[0],corners[2]-corners[0])
                normal /= np.linalg.norm(normal)
                assert np.allclose(normal,[0,-1,0])
            a,b = projected([[0,-.50,.535],[0,-1.45,.535]])
            arrow(d,a,b,CBLUE,width=5)
            text(d,(x+270,658),'Outward slide direction',23,CBLUE,True,anchor='ma')
            rule_lines = (['Fit a plane at the connection region.', 'Calculate its perpendicular direction.', 'Use that direction as the slide axis.'] if is_anymesh
                          else ['Drawer category → sliding joint.', 'Use the preset local slide axis.', 'Place it with the predicted part.'])
        else:
            candidates = np.array([[-.51,-.46,.20],[-.51,-.46,-.67],[.48,-.49,.20],[.48,-.49,-.67]])
            axis = projected([[-.51,-.46,.39],[-.51,-.46,-.88]])
            d.line([tuple(p) for p in axis],fill=CGOLD,width=5)
            if is_anymesh:
                assert np.allclose(np.cross(candidates[1]-candidates[0],[0,0,1]),0)
                for label,p,chosen in zip('ABCD',projected(candidates),[True,True,False,False]):
                    color = MODEL if chosen else MUTED
                    d.ellipse((p[0]-13,p[1]-13,p[0]+13,p[1]+13),fill=color if chosen else PAPER,outline=color,width=2)
                    d.text(tuple(p),label,font=font(18,True),fill='white' if chosen else MUTED,anchor='mm')
            # A short arc shows the same outward rotation used by mesh().
            arc=[]
            for angle in np.linspace(0,55,20):
                r,t=pose_transform('door',door=angle)
                arc.append(np.array([-.02,-.49,-.82])@r.T+t)
            arc=projected(arc)
            d.line([tuple(p) for p in arc],fill=CGOLD,width=4)
            arrow(d,arc[-3],arc[-1],CGOLD,width=4)
            text(d,(x+270,658),'Vertical hinge axis',23,CGOLD,True,anchor='ma')
            rule_lines = (['Take the selected 3D points A and B.', 'Fit a line through those points.', 'Use that line as the rotation axis.'] if is_anymesh
                          else ['Door category → rotating joint.', 'Use its preset local hinge axis.', 'Part placement locates the hinge.'])
        d.rounded_rectangle((x,715,x+540,907),radius=5,fill='#faf5ed',outline=PROGRAM,width=2)
        text(d,(x+16,731),'PROGRAM · '+('GEOMETRY' if is_anymesh else 'ASSEMBLY RULES'),22,PROGRAM,True)
        text(d,(x+16,776),rule_lines,24)
    text(d,(30,931),'Scripted teaching guides on the shared cabinet · no model inference is run.',21,MUTED)
    im.save(OUT/(method+'-joints.png'))
    mobile = Image.new('RGB',(600,1740),PAPER)
    md = ImageDraw.Draw(mobile)
    text(md,(30,24),'Articulate AnyMesh' if is_anymesh else 'URDFormer',29,bold=True)
    text(md,(30,68),'Model predictions and '+('geometry' if is_anymesh else 'assembly rules'),23,MUTED)
    for i,x in enumerate((30,630)):
        mobile.paste(im.crop((x,130,x+540,910)),(30,120+i*800))
    text(md,(30,1710),'Scripted cabinet example',20,MUTED)
    mobile.save(OUT/(method+'-joints-mobile.png'))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    validate(32)
    anymesh()
    boxes = urdformer()
    output_structure()
    joint_guides('anymesh')
    joint_guides('urdformer')
    (OUT/'manifest.json').write_text(json.dumps({
        'generator': 'scripts/draw_automatic_articulation.py',
        'geometry': 'scripts/shared_cabinet.py',
        'renderer': 'scripts/preview_shared_cabinet.py; opaque depth-tested triangles',
        'meaning': 'Authored teaching illustrations, not inference results from either research method.',
        'parts': ['body', 'drawer with fixed handle', 'door with fixed handle'],
        'moving_joints': ['drawer slide', 'door hinge'],
        'boxes': boxes,
        'urdformer_proxy': 'The canonical cabinet stands in for prepared part meshes. It is not the URDFormer asset library.',
        'joint_guides': 'Authored type predictions, connection plane, candidate points, and template axes explain responsibilities. A/B lie on the known canonical hinge. The plane normal is checked against the canonical slide direction. No axis estimation model is run.',
        'sources': ['https://articulate-anymesh.github.io/', 'https://arxiv.org/html/2502.02590v1#S3.SS3', 'https://urdformer.github.io/', 'https://github.com/WEIRDLabUW/urdformer/blob/main/utils.py']
    }, indent=2)+'\n')
    print('Rendered five articulation figures and four mobile layouts from the shared cabinet.')


if __name__ == '__main__':
    main()
