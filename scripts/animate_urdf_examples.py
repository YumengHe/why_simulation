#!/usr/bin/env python3
"""Render the chapter 4 GIFs from the shared teaching cabinet, without using PDF images.

Optional authoring dependencies: Pillow and NumPy. The book itself has no
dependencies. All poses are forward kinematics, not a contact simulation.
"""
from pathlib import Path
from math import cos, sin, pi
import argparse
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from draw_urdf_figures import load_geometry, Projection, C

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'book/assets/experiments'
WIDTH, HEIGHT, AA = 560, 540, 2
PAPER = (254, 253, 251)
FRAMES = 44
FRAME_COLORS = ('#b94242', '#357c4d', '#2c68ad')
MOTION_COLOR = '#7850a3'
AXES = {'outward': (0, 0, 1), 'inward': (0, 0, -1),
        'diagonal': (2**-.5, 2**-.5, 0)}
CASES = ('drawer-outward', 'drawer-inward', 'drawer-diagonal',
         'door-hinge', 'door-type-only', 'door-sliding',
         'drawer-present', 'drawer-removed', 'shapes-original', 'shapes-swapped')


def rotation(axis, angle):
    a = np.asarray(axis, float)
    a /= np.linalg.norm(a)
    x, y, z = a
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3)*cos(angle) + (1-cos(angle))*np.outer(a, a) + sin(angle)*skew


def pose(data, mesh, case, t):
    vertices = np.asarray(mesh['vertices'], float)
    link = mesh['link']
    if case == 'drawer-removed' and link == 'link_0':
        return None
    # The moved visual's new origin is -new_joint_origin for THIS model:
    # its saved geometry is in the parent frame, and both joint RPYs are zero.
    if case == 'shapes-swapped' and link in ('link_0', 'link_1'):
        link = 'link_1' if link == 'link_0' else 'link_0'
    if link == 'link_2':
        return vertices
    if link == 'link_0':
        active = case.startswith('drawer-') or case.startswith('shapes-')
        axis = AXES.get(case.removeprefix('drawer-'), AXES['outward'])
        return vertices + np.asarray(axis)*(.76*t if active else 0)
    active = case.startswith('door-') or case in (
        'drawer-present', 'drawer-removed', 'shapes-original', 'shapes-swapped')
    q = t if active else 0
    if case == 'door-type-only':
        return vertices + np.array([0, -1, 0])*1.5708*q
    if case == 'door-sliding':
        return vertices + np.array([1, 0, 0])*.7*q
    origin = np.asarray(data['joints']['joint_1']['origin'])
    return (vertices-origin) @ rotation((0, -1, 0), pi/2*q).T + origin


def camera(data, cases):
    # One camera per comparison, fixed throughout the entire animation.
    points = []
    for case in cases:
        for t in np.linspace(0, 1, 9):
            for mesh in data['meshes']:
                vs = pose(data, mesh, case, t)
                if vs is not None:
                    points.extend(vs)
    return Projection(points, (48, 65, WIDTH-96, HEIGHT-112), yaw=29, pitch=18)


def rgb(color):
    return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))


def face_layer(data, case, t, project, links):
    from raster_cabinet_legacy import layer
    return layer(data,lambda m:pose(data,m,case,t),project,links,(WIDTH,HEIGHT),AA)


def add_layer(base, layer, opacity=1):
    if opacity < 1:
        layer.putalpha(layer.getchannel('A').point(lambda value: round(value*opacity)))
    return Image.alpha_composite(base, layer)


def line(draw, points, color, width=2):
    draw.line([(int(x*AA), int(y*AA)) for x, y in points], fill=color, width=width*AA)


def arrow(draw, a, b, color):
    line(draw, [a, b], color, 3)
    d = np.asarray(b)-a
    if np.linalg.norm(d) < 1: return
    d /= np.linalg.norm(d)
    side = np.array([-d[1], d[0]])
    line(draw, [np.asarray(b)-d*11+side*5, b, np.asarray(b)-d*11-side*5], color, 3)


def font(size):
    for name in ('/System/Library/Fonts/Supplemental/Arial.ttf',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DejaVuSans.ttf'):
        try: return ImageFont.truetype(name, size*AA)
        except OSError: pass
    return ImageFont.load_default(size=size*AA)


def joint_axes(draw, origin, project):
    """Show the zero-pose joint frame, projected with the cabinet camera.

    The two moving joints in this specific asset have zero origin RPY, so
    their reference directions equal the body-frame basis. Keep these axes
    fixed while q changes: they show the reference pose, not a rotating child.
    """
    start = project(origin)
    # The arrows indicate directions, not distances. A fixed screen length
    # keeps the labels readable even in the long downward-travel example.
    length = 76 / project.scale
    offsets = ((19, -13), (0, -19), (-21, 16))
    for i, (name, color, offset) in enumerate(zip(('X', 'Y', 'Z'), FRAME_COLORS, offsets)):
        end = project(origin + np.eye(3)[i]*length)
        arrow(draw, start, end, rgb(color))
        draw.text(((end[0]+offset[0])*AA, (end[1]+offset[1])*AA),
                  '+'+name, fill=rgb(color), font=font(25), anchor='mm',
                  stroke_width=3*AA, stroke_fill=PAPER)
    x, y = start
    draw.ellipse(((x-4)*AA, (y-4)*AA, (x+4)*AA, (y+4)*AA),
                 fill=rgb(C['ink']), outline=PAPER, width=AA)


def render(data, case, t, project):
    frame = Image.new('RGBA', (WIDTH*AA, HEIGHT*AA), PAPER+(255,))
    frame = add_layer(frame, face_layer(data, case, t, project, {'link_2'}), .36)
    if case in ('drawer-outward', 'drawer-inward', 'drawer-diagonal'):
        frame = add_layer(frame, face_layer(data, case, t, project, {'link_1'}), .25)
        frame = add_layer(frame, face_layer(data, case, t, project, {'link_0'}))
    elif case.startswith('door-'):
        frame = add_layer(frame, face_layer(data, case, t, project, {'link_0'}), .48)
        frame = add_layer(frame, face_layer(data, case, t, project, {'link_1'}))
    else:
        frame = add_layer(frame, face_layer(data, case, t, project, {'link_0', 'link_1'}))
    draw = ImageDraw.Draw(frame)
    color = rgb(MOTION_COLOR)+(255,)
    origin = None
    legend = 'Purple arrow: slide direction'
    if case in ('drawer-outward', 'drawer-inward', 'drawer-diagonal'):
        origin = np.asarray(data['joints']['joint_0']['origin'])
        axis = np.asarray(AXES[case.removeprefix('drawer-')])
        a, b = project(origin), project(origin+axis*.76)
        arrow(draw, a, b, color)
        x, y = project(origin+axis*.76*t)
        draw.ellipse(((x-5)*AA, (y-5)*AA, (x+5)*AA, (y+5)*AA), fill=color)
        text = f'q = {round(76*t)} cm'
    elif case == 'door-hinge':
        origin = np.asarray(data['joints']['joint_1']['origin'])
        # -Y is the directed hinge axis. +Y is shown separately in the triad;
        # the door rotates ABOUT this line rather than translating along it.
        a, b = project(origin), project(origin+np.array([0, -.24, 0]))
        arrow(draw, a, b, color)
        text = f'q = {round(90*t)}°'
        legend = 'Purple arrow: hinge axis (-Y)'
    elif case in ('door-type-only', 'door-sliding'):
        origin = np.asarray(data['joints']['joint_1']['origin'])
        movement = np.array([0, -1.5708, 0]) if case == 'door-type-only' else np.array([.7, 0, 0])
        arrow(draw, project(origin), project(origin+movement), color)
        x, y = project(origin+movement*t)
        draw.ellipse(((x-5)*AA, (y-5)*AA, (x+5)*AA, (y+5)*AA), fill=color)
        text = f'q = {1.5708*t:.2f} m' if case == 'door-type-only' else f'q = {round(70*t)} cm'
    else: text = ''
    if origin is not None:
        joint_axes(draw, origin, project)
        draw.text((WIDTH/2*AA, 514*AA), legend, fill=rgb(MOTION_COLOR),
                  font=font(21), anchor='mm')
    if text:
        draw.text((WIDTH/2*AA, 19*AA), text, fill=rgb(C['ink']), font=font(25), anchor='mt')
    return frame.convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def check_poses(data):
    # This renderer's saved vertices and axis labels use the same body frame.
    for joint in ('joint_0', 'joint_1'):
        assert np.allclose(data['joints'][joint]['rpy'], [0, 0, 0])
    drawer = next(m for m in data['meshes'] if m['link'] == 'link_0')
    door = next(m for m in data['meshes'] if m['link'] == 'link_1')
    v = np.asarray(drawer['vertices'])
    for direction, axis in AXES.items():
        displacement = pose(data, drawer, 'drawer-'+direction, 1)-v
        assert np.allclose(displacement, np.asarray(axis)*.76)
        assert np.allclose(np.linalg.norm(displacement, axis=1), .76)
    for mesh in data['meshes']:
        assert np.allclose(pose(data, mesh, 'shapes-swapped', 0), mesh['vertices'])
    assert np.allclose(pose(data, door, 'door-type-only', 1)-door['vertices'], [0, -1.5708, 0])
    assert np.allclose(pose(data, door, 'door-sliding', 1)-door['vertices'], [.7, 0, 0])
    assert pose(data, drawer, 'drawer-removed', .5) is None
    assert np.allclose(pose(data, door, 'drawer-present', .6), pose(data, door, 'drawer-removed', .6))
    hinge = np.asarray(data['joints']['joint_1']['origin'])
    swapped = pose(data, drawer, 'shapes-swapped', .7)
    assert np.allclose(np.linalg.norm(swapped-hinge, axis=1), np.linalg.norm(v-hinge, axis=1))
    assert np.allclose(pose(data, door, 'shapes-swapped', 1)-door['vertices'], [0, 0, .76])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=CASES)
    parser.add_argument('--check', action='store_true', help='Check the example motions without rendering')
    args = parser.parse_args()
    data = load_geometry(); check_poses(data)
    if args.check:
        print('All example motions agree with their joint settings.'); return
    OUT.mkdir(parents=True, exist_ok=True)
    cameras = {}
    for group in (CASES[:3], ('drawer-present', 'drawer-removed'), ('shapes-original', 'shapes-swapped')):
        project = camera(data, group)
        for case in group: cameras[case] = project
    for case in CASES[3:6]: cameras[case] = camera(data, (case,))
    # Slow opening/closing, with a brief hold at both ends. Every clip has the
    # same timing; the GIF loop begins and ends in the closed pose.
    positions = [(1-cos(pi*i/(FRAMES-1)))/2 for i in range(FRAMES)]
    for case in ((args.only,) if args.only else CASES):
        opening = [render(data, case, t, cameras[case]) for t in positions]
        frames = opening + opening[-2:0:-1]
        # A shared palette avoids color flicker between GIF frames.
        sample = Image.new('RGB', (WIDTH*5, HEIGHT))
        for i, index in enumerate(np.linspace(0, FRAMES-1, 5).astype(int)):
            sample.paste(opening[index], (WIDTH*i, 0))
        palette = sample.quantize(colors=192, method=Image.Quantize.MEDIANCUT)
        indexed = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames]
        durations = [60]*len(frames); durations[0] = durations[FRAMES-1] = 650
        indexed[0].save(OUT/f'{case}.gif', save_all=True, append_images=indexed[1:],
                        duration=durations, loop=0, optimize=True, disposal=1)
        opening[-1].save(OUT/f'{case}.png', optimize=True)
        print(f'{case}: {(OUT/f"{case}.gif").stat().st_size/1024:.0f} KB', flush=True)
    manifest = dict(source=data['source'], size=[WIDTH, HEIGHT], frames=FRAMES*2-2,
                    duration_ms=sum([60]*(FRAMES*2-2))+2*(650-60),
                    rendering='Forward kinematics; cabinet shown translucent; no collision response',
                    axis_annotations='Moving-joint reference frame at q=0: X red, Y green, Z blue; motion axis purple',
                    examples=list(CASES))
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    main()
