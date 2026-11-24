#!/usr/bin/env python3
"""Draw software layers and task concepts with the shared cabinet.

All layouts, geometry and poses are authored. No physics or robot policy is
run; these are teaching diagrams, not screenshots of the named systems.
"""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw
from shared_cabinet import mesh, validate, CabinetMesh, part_triangles, DRAWER_LIMIT
from preview_shared_cabinet import render, font

OUT = Path(__file__).resolve().parents[1] / 'book/assets/simulation-platforms'
PAPER = (254, 253, 251)
INK, MUTED, LINE = '#293632', '#626963', '#d8ddd7'
BLUE, TEAL, GOLD, PURPLE = '#39759e', '#467e79', '#9b741f', '#805095'


def label(d, x, y, lines, size=24, color=INK, bold=False):
    if isinstance(lines, str):
        lines = [lines]
    for i, line in enumerate(lines):
        d.text((x, y+i*(size+9)), line, font=font(size, bold), fill=color)


def arrow(d, a, b, color=MUTED, width=3):
    a, b = np.array(a, float), np.array(b, float)
    u = (b-a)/np.linalg.norm(b-a); v = np.array([-u[1], u[0]])
    d.line([tuple(a), tuple(b)], fill=color, width=width)
    d.polygon([tuple(b), tuple(b-11*u+5*v), tuple(b-11*u-5*v)], fill=color)


def canvas(size, title, subtitle, title_size=33):
    im = Image.new('RGB', size, PAPER); d = ImageDraw.Draw(im)
    label(d, 30, 25, title, title_size, bold=True)
    label(d, 30, 73, subtitle, 23, MUTED)
    return im, d


def box(d, rect, heading, lines, color=TEAL, fill='#f3f7f5', small=None):
    x, y, right, bottom = rect
    d.rounded_rectangle(rect, radius=8, fill=fill, outline=color, width=2)
    if small:
        label(d, x+20, y+15, small, 18, color, True)
    hy = y+45 if small else y+18
    label(d, x+20, hy, heading, 28, color, True)
    for i, line in enumerate(lines):
        assert d.textlength(line, font=font(23)) <= right-x-40, line
        label(d, x+20, hy+43+i*31, line, 23)


def layers():
    im, d = canvas((1200,1000), 'From physical motion to a robot task',
                   'Each task environment uses the software below it.')
    box(d, (30,119,1170,233), 'Policy: choose the next action',
        ['Read an observation; request a robot movement.'], PURPLE, '#f5f1f8')
    branches = [
        ('ManiSkill route', [('ManiSkill', ['Manipulation tasks, observations,', 'actions, rewards, and success checks.']),
         ('SAPIEN', ['Scene objects, cameras, rendering,', 'and access to physics.']),
         ('PhysX', ['Forces, contacts, joint constraints,', 'and the next physical state.'])]),
        ('RoboCasa route', [('RoboCasa', ['Kitchen tasks, scene variation,', 'demonstrations, and evaluation.']),
         ('robosuite', ['Robot models, controllers,', 'and observation interfaces.']),
         ('MuJoCo', ['Forces, contacts, joint constraints,', 'and the next physical state.'])])]
    roles = ['TASK ENVIRONMENT', 'SCENE / ROBOT SUPPORT', 'PHYSICS ENGINE']
    for col, (title, rows) in enumerate(branches):
        x = 30+600*col; mid=x+270
        arrow(d, (mid,237), (mid,271), PURPLE)
        label(d, x+10, 281, title, 26, bold=True)
        for i, (name, desc) in enumerate(rows):
            y = 330+205*i
            color = GOLD if i==2 else TEAL
            box(d, (x,y,x+540,y+157), name, desc, color,
                '#faf6ec' if i==2 else '#f3f7f5', roles[i])
            if i<2:
                arrow(d, (mid,y+163), (mid,y+199))
                label(d, mid+16, y+164, 'uses', 19, MUTED)
    label(d, 30, 947, 'Responsibilities overlap: MuJoCo also provides rendering and visualization.', 22, MUTED)
    im.save(OUT/'software-layers.png')
    mobile, md = canvas((600,1750), 'Software layers', 'Two routes from a task to physics.')
    box(md, (30,119,570,233), 'Policy', ['Observation → chosen action'], PURPLE, '#f5f1f8')
    for col, (title, rows) in enumerate(branches):
        top = 280+695*col
        label(md, 30, top, title, 28, bold=True)
        for i, (name, desc) in enumerate(rows):
            y=top+55+190*i; color=GOLD if i==2 else TEAL
            box(md, (30,y,570,y+157), name, desc, color,
                '#faf6ec' if i==2 else '#f3f7f5', roles[i])
            if i<2:
                arrow(md,(300,y+159),(300,y+187));label(md,318,y+160,'uses',18,MUTED)
    label(md,30,1645,['The rows show each package’s main role.',
                      'Packages can also cover other roles.'],23,MUTED)
    mobile.save(OUT/'software-layers-mobile.png')


def cabinet(q, size=(330,350), scale=145):
    assert 0<=q<=DRAWER_LIMIT
    return render(mesh(drawer=q), size=size, scale=scale, center=(0,-.32,0), ss=2)


def physics():
    im,d=canvas((1200,760),'One short physics step','The physical model and control inputs determine the update.')
    for x in (30,420,810):
        d.rectangle((x,138,x+360,670),outline=LINE,width=2)
    label(d,48,160,'1  Current state',27,BLUE,True)
    im.paste(cabinet(.12),(45,217))
    label(d,48,584,['Drawer opening and speed', 'Robot positions and speeds'],21)
    label(d,438,160,'2  Physics engine',27,GOLD,True)
    for y, head, lines in [(244,'Find contacts',['Where do the collision','shapes meet?']),
                          (366,'Solve the response',['Motor and contact forces,','friction, and joint constraints']),
                          (488,'Advance motion',['Update velocities','and positions.'])]:
        label(d,442,y,head,24,GOLD,True);label(d,442,y+39,lines,21)
    label(d,828,160,'3  Next state',27,BLUE,True)
    im.paste(cabinet(.23),(825,217))
    label(d,828,584,['Updated drawer opening', 'and robot / drawer speeds'],21)
    d=ImageDraw.Draw(im)
    arrow(d,(392,404),(416,404));arrow(d,(782,404),(806,404))
    label(d,30,706,'Repeat from the updated state. Cabinet poses here illustrate the process.',23,MUTED)
    im.save(OUT/'physics-step.png')
    mobile,md=canvas((600,1650),'One short physics step','Current state → calculation → next state')
    for i,head in enumerate(['1  Current state','2  Physics engine','3  Next state']):
        y=135+i*490
        md.rectangle((30,y,570,y+450),outline=LINE,width=2)
        label(md,50,y+16,head,28,BLUE if i!=1 else GOLD,True)
        if i!=1:
            mobile.paste(cabinet(.12 if i==0 else .23,size=(300,305),scale=128),(150,y+62))
            label(md,50,y+380,['Drawer opening and speed','Robot positions and speeds'] if i==0 else
                  ['Updated drawer opening','and robot / drawer speeds'],23)
        else:
            for j,(head,desc) in enumerate([('Find contacts','Where do collision shapes meet?'),
                                           ('Solve the response','Forces, friction, and joint constraints'),
                                           ('Advance motion','Update velocities and positions.')]):
                label(md,50,y+86+j*112,head,26,GOLD,True)
                label(md,50,y+129+j*112,desc,23)
        if i<2:arrow(md,(300,y+456),(300,y+484))
    label(md,30,1610,'Illustrated states; no physics engine is run.',21,MUTED)
    mobile.save(OUT/'physics-step-mobile.png')


def kitchen(stage):
    """Add an explicit open cup and counter to the unchanged cabinet."""
    m=mesh(drawer=.70)
    ts=list(m.triangles); cs=list(m.colors); gs=list(m.groups); ns=list(m.names)
    def append(tris,color,name):
        ts.extend(tris);cs.extend([color]*len(tris));gs.extend(['prop']*len(tris));ns.extend([name]*len(tris))
    for name,lo,hi in [('counter-top',(.80,-.15,.72),(1.75,.55,.79)),
                       ('counter-left',(.83,-.08,-.86),(.91,.48,.72)),
                       ('counter-right',(1.64,-.08,-.86),(1.72,.48,.72))]:
        append(part_triangles(dict(kind='box',lo=lo,hi=hi)),(180,165,140),name)
    base=np.array([(0,-.68,.39),(0,-.85,1.08),(1.25,.1,.79)][stage])
    outer,inner,height=.115,.09,.27
    cup=[]
    def quad(a,b,c,e):cup.extend([[a,b,c],[a,c,e]])
    for i in range(32):
        a=2*math.pi*i/32;b=2*math.pi*(i+1)/32
        def p(r,t,z):return base+np.array([r*math.cos(t),r*math.sin(t),z])
        quad(p(outer,a,0),p(outer,b,0),p(outer,b,height),p(outer,a,height))
        quad(p(inner,a,.025),p(inner,a,height),p(inner,b,height),p(inner,b,.025))
        quad(p(outer,a,height),p(outer,b,height),p(inner,b,height),p(inner,a,height))
        cup.append([base+[0,0,.025],p(inner,a,.025),p(inner,b,.025)])
        cup.append([base,p(outer,b,0),p(outer,a,0)])
    append(np.array(cup),(218,124,75),'cup')
    model=CabinetMesh(np.array(ts),np.array(cs),np.array(gs),np.array(ns))
    return render(model,size=(360,285),eye=(3,-6,4.5),center=(.45,-.30,.12),scale=109,ss=2)


def tasks():
    im,d=canvas((1200,990),'From one skill to a kitchen activity','Use the same cabinet to make task definitions concrete.')
    d.rectangle((30,115,1170,462),outline=LINE,width=2)
    im.paste(cabinet(.70,size=(325,315),scale=132),(40,135))
    label(d,398,140,'ManiSkill example: open the target drawer',28,TEAL,True)
    label(d,398,190,['The task checks opening AND low motion.',
                     '90% of the opening range is the threshold.'],25)
    x0,x1,y=400,1115,325
    d.rounded_rectangle((x0,y,x1,y+29),radius=4,fill='#e8ece9')
    threshold=x0+(x1-x0)*.9
    d.rectangle((x0,y,threshold,y+29),fill=BLUE)
    d.line((threshold,y-12,threshold,y+45),fill=GOLD,width=3)
    label(d,x0,y+47,'Closed',21,MUTED)
    label(d,threshold-35,y-48,'90%',25,GOLD,True)
    label(d,x1-92,y+47,'Full range',21,MUTED)
    label(d,398,416,'Teaching cabinet: 0.90 × 76 cm = 68.4 cm',23)
    label(d,30,497,'RoboCasa-style teaching activity: complete several actions',28,TEAL,True)
    for i,head in enumerate(['1  Open the drawer','2  Take out the cup','3  Place on the counter']):
        x=30+i*390
        d.rectangle((x,550,x+360,912),outline=LINE,width=2)
        label(d,x+16,570,head,24,BLUE,True)
        im.paste(kitchen(i),(x,615))
        d.rectangle((x,550,x+360,912),outline=LINE,width=2)
    d=ImageDraw.Draw(im)
    arrow(d,(393,733),(416,733));arrow(d,(783,733),(806,733))
    label(d,30,942,'Scripted task illustrations. Cup poses are staged; robot motion is omitted.',22,MUTED)
    im.save(OUT/'cabinet-tasks.png')
    mobile,md=canvas((600,1760),'Cabinet task examples','Task rules define the required result.')
    label(md,30,126,'ManiSkill: target drawer',28,TEAL,True)
    mobile.paste(cabinet(.70,size=(255,275),scale=113),(170,176))
    label(md,30,466,['Success: at least 90% open,','with sufficiently small motion.'],25)
    label(md,30,551,'Example: 68.4 cm of a 76 cm range',23,MUTED)
    label(md,30,615,'Kitchen activity: three actions',27,TEAL,True)
    for i,head in enumerate(['1  Open the drawer','2  Take out the cup','3  Place on the counter']):
        y=675+i*340
        label(md,30,y,head,25,BLUE,True)
        mobile.paste(kitchen(i),(120,y+38))
    label(md,30,1710,'Staged poses; this illustrates a task.',22,MUTED)
    mobile.save(OUT/'cabinet-tasks-mobile.png')


def loop():
    im,d=canvas((1200,780),'One interaction in a robot task','An action is executed; its outcome becomes the next observation.')
    entries=[('1  Observation',['Camera image','or state values'],TEAL),
             ('2  Policy',['Choose an action:','“Pull outward.”'],PURPLE),
             ('3  Controller',['Translate the movement','into motor control inputs.'],BLUE),
             ('4  Physics',['Calculate contact and motion','over short time steps.'],GOLD),
             ('5  Task feedback',['New image / state values','Reward and success'],TEAL)]
    places=[(30,170,370,350),(430,170,770,350),(830,170,1170,350),
            (830,450,1170,635),(430,450,770,635)]
    for (head,desc,color),rect in zip(entries,places):
        box(d,rect,head,desc,color)
    arrow(d,(375,260),(424,260));arrow(d,(775,260),(824,260))
    arrow(d,(1000,357),(1000,441));arrow(d,(824,542),(776,542))
    d.line([(426,542),(199,542),(199,358)],fill=TEAL,width=3)
    arrow(d,(199,389),(199,358),TEAL)
    label(d,34,584,['Next observation','while the episode continues'],22,TEAL)
    label(d,30,694,'End the attempt using the experiment’s stopping rule or time limit; then reset.',23,MUTED)
    im.save(OUT/'interaction-loop.png')
    mobile,md=canvas((600,1450),'A task interaction','Observe → act → simulate → observe again')
    for i,(head,desc,color) in enumerate(entries):
        y=140+i*225
        box(md,(45,y,555,y+165),head,desc,color)
        if i<4:arrow(md,(300,y+172),(300,y+217))
    label(md,30,1295,['Use the new observation for the next action.',
                       'End at the stopping condition or time limit.',
                       'Reset to start another attempt.'],23,MUTED)
    mobile.save(OUT/'interaction-loop-mobile.png')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    validate(32)
    assert math.isclose(.9*DRAWER_LIMIT,.684)
    layers(); physics(); tasks(); loop()
    manifest={'source':'scripts/draw_simulation_platforms.py',
              'model':'scripts/shared_cabinet.py',
              'provenance':'Authored diagrams with depth-tested cabinet, cup and counter meshes. No engine, task environment or policy is executed.',
              'drawer_travel_m':DRAWER_LIMIT,'illustrative_90_percent_opening_m':.9*DRAWER_LIMIT,
              'sources':['https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/quickstart.html',
                         'https://maniskill.readthedocs.io/en/latest/api/mani_skill/envs/tasks/mobile_manipulation/open_cabinet_drawer/index.html',
                         'https://github.com/haosulab/SAPIEN',
                         'https://robosuite.ai/docs/overview.html',
                         'https://github.com/robocasa/robocasa',
                         'https://mujoco.readthedocs.io/en/stable/computation/index.html']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Rendered four diagrams and four mobile layouts from explicit code and geometry.')


if __name__=='__main__':main()
