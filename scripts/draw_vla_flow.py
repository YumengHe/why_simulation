#!/usr/bin/env python3
"""Draw the two static, schematic views in the VLA teaching flow."""
from pathlib import Path
from math import atan2, acos, cos, sin, hypot

OUT = Path(__file__).resolve().parents[1] / 'book/assets/diagrams'
OUT.mkdir(parents=True, exist_ok=True)


def scene(opening_cm):
    shift = opening_cm * 4
    hand_x = 248 + shift
    sx, sy, tx, ty, a, b = 494, 250, hand_x + 45, 140, 145, 130
    d = hypot(tx-sx, ty-sy)
    angle = atan2(ty-sy, tx-sx) + acos((a*a+d*d-b*b)/(2*a*d))
    ex, ey = sx+a*cos(angle), sy+a*sin(angle)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 310" role="img">
  <title>Drawer {opening_cm} cm open; gripper holding the handle</title>
  <path d="M30 267H535" stroke="#e8e5de" stroke-width="2"/>
  <rect x="55" y="83" width="180" height="179" rx="2" fill="#dbe7e3" stroke="#759c94" stroke-width="2"/>
  <rect x="68" y="185" width="154" height="66" fill="#e8d7a8" stroke="#c5a65a"/>
  <path d="M77 177H219" stroke="#759c94" stroke-width="4"/>
  <g transform="translate({shift} 0)">
    <rect x="72" y="111" width="158" height="57" fill="#e4edf3" stroke="#5b8db8" stroke-width="2"/>
    <path d="M72 111V168H230" fill="none" stroke="#5b8db8" stroke-width="4"/>
    <rect x="222" y="102" width="13" height="75" fill="#5b8db8"/>
    <path d="M235 130H248V151H235" fill="none" stroke="#3e6380" stroke-width="5"/>
  </g>
  <path d="M494 250V267M477 267H514" fill="none" stroke="#637278" stroke-width="10" stroke-linecap="round"/>
  <path d="M{sx} {sy}L{ex:.3f} {ey:.3f}L{tx} {ty}" fill="none" stroke="#b7bec0" stroke-width="15" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="{ex:.3f}" cy="{ey:.3f}" r="9" fill="#718288"/>
  <circle cx="494" cy="250" r="10" fill="#718288"/>
  <g transform="translate({hand_x} 0)">
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
