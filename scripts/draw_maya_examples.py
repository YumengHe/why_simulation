#!/usr/bin/env python3
"""Draw shared Blender/Maya examples of rig controls, keyframes and curves.

These are original SVG diagrams, not application screenshots or simulation results.
The arm uses a planar two-link IK solution with fixed segment lengths. Drawer
curves compare q=40*u and q=40*(3*u*u-2*u*u*u), where u=t/2.
"""
from pathlib import Path
from math import acos, atan2, cos, sin, hypot
from html import escape

OUT = Path(__file__).resolve().parents[1] / 'book/assets/maya'
OUT.mkdir(parents=True, exist_ok=True)
INK, MUTED, LINE = '#252824', '#656b66', '#deddd5'
BLUE, GOLD, TEAL = '#5b8db8', '#a57b24', '#83a6a0'


def text(x, y, value, size=22, color=INK, anchor='start', weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(value)}</text>'


def path(d, color=LINE, width=2, fill='none', extra=''):
    return f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="{fill}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def save(name, title, body, height):
    (OUT / f'{name}.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 {height}" role="img">
<title>{escape(title)}</title>
<rect width="960" height="{height}" fill="#fdfcf9"/>
<g font-family="Arial, Helvetica, sans-serif">{body}</g></svg>\n''')


def cabinet(q=0):
    from shared_cabinet_views import side
    return side(drawer=q/100,scale=119,xy=(142.69,232.6))


def arm(wrist):
    sx, sy = 405, 335
    tx, ty = wrist
    a, b = 165, 145
    d = hypot(tx-sx, ty-sy)
    theta = atan2(ty-sy, tx-sx) - acos((a*a+d*d-b*b)/(2*a*d))
    ex, ey = sx+a*cos(theta), sy+a*sin(theta)
    assert abs(hypot(ex-sx, ey-sy)-a) < 1e-9
    assert abs(hypot(ex-tx, ey-ty)-b) < 1e-9
    drawing = path(f'M{sx} {sy}L{ex:.3f} {ey:.3f}L{tx} {ty}', '#97a9b2', 21)
    drawing += path(f'M{sx} {sy}L{ex:.3f} {ey:.3f}L{tx} {ty}', GOLD, 3)
    for x, y in ((sx, sy), (ex, ey), wrist):
        drawing += f'<circle cx="{x:.3f}" cy="{y:.3f}" r="7" fill="#fffaf0" stroke="{GOLD}" stroke-width="3"/>'
    drawing += path('M389 345H425', '#61727b', 12)
    drawing += path(f'M{tx} {ty-14}H{tx-27}V{ty-5}M{tx} {ty+14}H{tx-27}V{ty+5}', '#61727b', 6)
    drawing += f'<rect x="{tx-41}" y="{ty-24}" width="54" height="48" rx="7" stroke="{GOLD}" stroke-width="2.5" fill="none" stroke-dasharray="5 4"/>'
    return drawing


body = text(28, 40, 'After rigging: move the hand control to pose the arm', 27, weight=600)
body += text(28, 72, 'A mechanical arm beside the cabinet · side cutaway', 20, MUTED)
body += path('M480 95V428')
for x, wrist, heading in ((0, (333, 165), 'Before: hand away from the handle'), (480, (247, 169.5), 'After: hand at the handle')):
    panel = text(26, 112, heading, 22, weight=600)
    panel += cabinet() + arm(wrist)
    if x == 0:
        panel += text(234, 387, 'Hand control', 21, GOLD)
        panel += path('M306 365L346 194', GOLD, 1.5)
    else:
        panel += text(222, 387, 'Arm joints follow', 20, GOLD)
        panel += path('M285 365L256 315', GOLD, 1.5)
    body += f'<g transform="translate({x} 20)">{panel}</g>'
save('arm-ik', 'Two poses of an arm rig: moving the hand control changes the shoulder and elbow angles', body, 460)

body = text(28, 40, 'Choose two drawer positions and their times', 27, weight=600)
for i, (t, q) in enumerate(((0, 0), (1, 20), (2, 40))):
    x = i*320
    label = 'Calculated in between' if i == 1 else 'Keyframe'
    panel = text(160, 87, label, 23, BLUE if i == 1 else GOLD, 'middle', 600)
    panel += '<g transform="translate(5 -24)">' + cabinet(q) + '</g>'
    panel += text(160, 362, f'{t} s · {q} cm open', 24, INK, 'middle', 600)
    body += f'<g transform="translate({x} 0)">{panel}</g>'
body += path('M145 398H815', '#a9aaa2', 2)
for x in (160, 800):
    body += f'<path d="M{x} 389l9 9-9 9-9-9z" fill="{GOLD}"/>'
body += f'<circle cx="480" cy="398" r="5" fill="{BLUE}"/>'
body += text(480, 441, 'For constant speed: 20 cm each second', 21, MUTED, 'middle')
save('drawer-keyframes', 'Drawer animation at zero, one and two seconds, with keyframes at zero and two', body, 470)

body = text(28, 40, 'Same starting and ending positions; different timing', 27, weight=600)
body += text(58, 88, 'Drawer opening (cm)', 21, INK)
x0, y0, w, h = 86, 337, 510, 220
for q in (0, 20, 40):
    y = y0-h*q/40
    body += path(f'M{x0} {y}H{x0+w}', LINE, 1.5)
    body += text(67, y+7, str(q), 20, MUTED, 'end')
for t in (0, 1, 2):
    x = x0+w*t/2
    body += path(f'M{x} {y0}V{y0+7}', MUTED, 1.5)
    body += text(x, y0+32, str(t), 20, MUTED, 'middle')
body += text(x0+w/2, 408, 'Time (seconds)', 21, INK, 'middle')
body += path(f'M{x0} {y0-h}V{y0}H{x0+w}', MUTED, 2)
body += path(f'M{x0} {y0}L{x0+w} {y0-h}', BLUE, 4)
curve=[]
for i in range(101):
    u=i/100
    q=3*u*u-2*u*u*u
    curve.append(f'{"M" if not i else "L"}{x0+w*u:.3f} {y0-h*q:.3f}')
body += path(' '.join(curve), GOLD, 4)
for x,y in ((x0,y0),(x0+w,y0-h)):
    body += f'<circle cx="{x}" cy="{y}" r="6" fill="{INK}"/>'
body += path('M646 135H691', BLUE, 4) + text(708, 142, 'Constant speed', 22, BLUE, weight=600)
body += text(646, 178, 'Equal movement each second.', 20, MUTED)
body += path('M646 224H691', GOLD, 4) + text(708, 231, 'Ease in / out', 22, GOLD, weight=600)
body += text(646, 267, 'Start slowly, speed up,', 20, MUTED)
body += text(646, 296, 'then slow down before stopping.', 20, MUTED)
body += text(646, 363, 'A steeper line means', 20, INK)
body += text(646, 392, 'faster drawer movement.', 20, INK)
body += text(480, 458, 'Edit the curve to change how the movement feels.', 22, INK, 'middle')
save('drawer-curves', 'Drawer opening against time: a straight line gives constant speed while an S curve eases in and out', body, 490)
print('Wrote three shared Blender/Maya animation teaching diagrams.')
