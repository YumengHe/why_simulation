#!/usr/bin/env python3
"""Export cabinet-only panels for the native HTML diagrams.

Crops retain the geometry and spatial guides from the original scripted plates.
All headings, stages, explanations and connections are now native page content.
"""
from pathlib import Path
from PIL import Image
from draw_simulation_platforms import cabinet, kitchen

ASSETS = Path(__file__).resolve().parents[1]/'book/assets'
OUT = ASSETS/'diagram-panels'


def main():
    OUT.mkdir(exist_ok=True)
    def crop(source, rect, name):
        with Image.open(ASSETS/source) as im:
            im.crop(rect).save(OUT/(name+'.png'))
    for name,x in [('anymesh-input',30),('anymesh-parts',420),('articulated-output',810)]:
        crop('automatic-articulation/anymesh-cabinet.png',(x,211,x+360,585),name)
    crop('automatic-articulation/urdformer-cabinet.png',(30,211,390,585),'detected-parts')
    for method in ('anymesh','urdformer'):
        for part,x in [('drawer',30),('door',630)]:
            crop(f'automatic-articulation/{method}-joints.png',(x,275,x+540,647),f'{method}-{part}')
    crop('automatic-articulation/cabinet-output.png',(30,132,530,582),'cabinet-structure')
    for name,q in [('physics-current',.12),('physics-next',.23),('task-open',.70)]:
        cabinet(q).save(OUT/(name+'.png'))
    for i in range(3):
        kitchen(i).save(OUT/f'kitchen-{i}.png')
    print('Exported 15 scripted cabinet panels for responsive diagrams.')


if __name__ == '__main__':
    main()
