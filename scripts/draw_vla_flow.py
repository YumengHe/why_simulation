#!/usr/bin/env python3
"""Draw the two static, schematic views in the VLA teaching flow."""
from pathlib import Path
from math import atan2, acos, cos, sin, hypot

OUT = Path(__file__).resolve().parents[1] / 'book/assets/diagrams'
OUT.mkdir(parents=True, exist_ok=True)


def scene(opening_cm):
    shift = opening_cm * 1.1
    hand_x = 239.6 + shift
    sx, sy, tx, ty, a, b = 494, 250, hand_x + 45, 109.1, 145, 130
    d = hypot(tx-sx, ty-sy)
    angle = atan2(ty-sy, tx-sx) + acos((a*a+d*d-b*b)/(2*a*d))
    ex, ey = sx+a*cos(angle), sy+a*sin(angle)
    from shared_cabinet_views import side
    cabinet = side(drawer=opening_cm/100,scale=110,xy=(168.1,167.4))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 310" role="img">
  <title>Side cutaway: drawer {opening_cm} cm open; gripper holding the fixed handle</title>
  <path d="M30 267H535" stroke="#e8e5de" stroke-width="2"/>
  {cabinet}
  <path d="M494 250V267M477 267H514" fill="none" stroke="#637278" stroke-width="10" stroke-linecap="round"/>
  <path d="M{sx} {sy}L{ex:.3f} {ey:.3f}L{tx} {ty}" fill="none" stroke="#b7bec0" stroke-width="15" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="{ex:.3f}" cy="{ey:.3f}" r="9" fill="#718288"/>
  <circle cx="494" cy="250" r="10" fill="#718288"/>
  <g transform="translate({hand_x} -30.9)">
    <path d="M33 140H45" stroke="#637278" stroke-width="9"/>
    <rect x="23" y="117" width="11" height="47" rx="3" fill="#637278"/>
    <path d="M27 132H-5V138M27 148H-5V142" fill="none" stroke="#637278" stroke-width="6" stroke-linejoin="round"/>
  </g>
  <path d="M329 286H429M422 280L429 286L422 292" fill="none" stroke="#9a7422" stroke-width="2"/>
  <text x="219" y="294" fill="#71654c" font-size="26" font-family="sans-serif">Outward</text>
</svg>
'''


for label, opening in [('before', 0), ('after', 10)]:
    (OUT / f'vla-drawer-{label}.svg').write_text(scene(opening))
print('Wrote static before/after drawer diagrams.')
