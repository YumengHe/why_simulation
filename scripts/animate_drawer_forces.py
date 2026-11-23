#!/usr/bin/env python3
"""Calculate one-dimensional drawer motion and render original teaching GIFs.

Optional authoring dependency: Pillow. Geometry is a side-view diagram, not
measured cabinet geometry. Dynamics use chosen mass and Coulomb rail friction,
an applied force pulse, and inelastic travel stops at 0 and 0.76 m.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import json
import math

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / 'book/assets/forces'
W, H, AA = 560, 430, 2
DT, FPS, LIMIT = .001, 25, .76
PAPER = '#fefdfb'
INK, MUTED, LINE = '#303630', '#716d63', '#ded9ce'
BLUE, BLUE_DARK, TEAL = '#b8d2e4', '#4e7d9d', '#d7e4de'
PULL, FRICTION = '#377960', '#b36734'


@dataclass(frozen=True)
class Case:
    title: str
    mass: float = 2
    pull: float = 3
    static: float = 0
    kinetic: float = 0
    q0: float = 0
    v0: float = 0
    duration: float = 1


PAIRS = {
    'stronger-pull': (Case('Gentle pull', pull=1), Case('Stronger pull')),
    'heavier-drawer': (Case('Lighter drawer'), Case('Heavier drawer', mass=4)),
    'rail-friction': (Case('Easy-sliding rails', static=1, kinetic=.8),
                      Case('Stiff rails', static=4, kinetic=3)),
    'after-release': (Case('No friction', pull=0, q0=.1, v0=.4, duration=1.5),
                      Case('With friction', pull=0, static=1, kinetic=.8,
                           q0=.1, v0=.4, duration=1.5)),
}


def pull_at(case, t):
    return case.pull if t < .5 - 1e-9 else 0


def friction_at(case, v, force):
    if abs(v) < 1e-10 and abs(force) <= case.static:
        return -force
    return -math.copysign(case.kinetic, v if abs(v) > 1e-10 else force)


def advance(case, q, v, force, dt):
    """Integrate a constant-force segment; resolve sticking and stops.

    Within a sliding segment the acceleration is constant, so use the exact
    constant-acceleration update. Resolve the moment velocity reaches zero
    to avoid friction reversing the drawer. Pulse transitions align with DT.
    """
    friction = friction_at(case, v, force)
    a = (force + friction) / case.mass
    if v * (v + a * dt) < 0:
        stop_time = -v / a
        q += v * stop_time + .5 * a * stop_time**2
        return advance(case, q, 0, force, dt - stop_time)
    q += v * dt + .5 * a * dt**2
    v += a * dt
    if abs(v) < 1e-10: v = 0
    if q >= LIMIT: return LIMIT, min(v, 0)
    if q <= 0: return 0, max(v, 0)
    return q, v


def simulate(case):
    q, v, samples = case.q0, case.v0, []
    stride = round(1 / FPS / DT)
    for i in range(round(case.duration / DT) + 1):
        t = i * DT
        force = pull_at(case, t)
        if i % stride == 0 or i == round(case.duration / DT):
            samples.append(dict(t=round(t, 6), q=q, v=v, pull=force,
                                friction=friction_at(case, v, force)))
        q, v = advance(case, q, v, force, DT)
    return samples


def check():
    # Independent closed-form expectations: q = F/m*(T*t - T*T/2)
    # after a T=.5 s force pulse, without friction; all start at rest.
    weak, strong = [simulate(c) for c in PAIRS['stronger-pull']]
    assert abs(weak[-1]['q'] - .1875) < 1e-8
    assert abs(strong[-1]['q'] - .5625) < 1e-8
    assert abs(simulate(PAIRS['heavier-drawer'][1])[-1]['q'] - .28125) < 1e-8
    sticky = simulate(PAIRS['rail-friction'][1])
    assert all(s['q'] == s['v'] == 0 for s in sticky)
    assert all(s['friction'] == -s['pull'] for s in sticky)
    assert abs(simulate(PAIRS['rail-friction'][0])[-1]['q'] - .3625) < 1e-8
    coast, stop = [simulate(c) for c in PAIRS['after-release']]
    assert abs(coast[-1]['q'] - .7) < 1e-8
    # Stopping distance v^2/(2a) = .2 m, on top of q0=.1 m.
    assert abs(stop[-1]['q'] - .3) < 1e-8 and stop[-1]['v'] == 0
    assert all(s['v'] >= 0 for s in stop)
    assert all(abs(s['v'] - .4) < 1e-10 for s in coast)
    for pair in PAIRS.values():
        for case in pair:
            assert all(0 <= s['q'] <= LIMIT for s in simulate(case))
    limit_case = simulate(Case('Travel stop', pull=100, duration=2))
    assert limit_case[-1]['q'] == LIMIT and limit_case[-1]['v'] == 0
    print('Force, mass, sticking, stopping distance, coasting, and travel limits pass.')


def font(size, bold=False):
    names = [f'/System/Library/Fonts/Supplemental/Arial{" Bold" if bold else ""}.ttf',
             f'/usr/share/fonts/truetype/dejavu/DejaVuSans{"-Bold" if bold else ""}.ttf']
    for name in names:
        try: return ImageFont.truetype(name, round(size * AA))
        except OSError: pass
    return ImageFont.load_default(size=round(size * AA))


def panel(case, sample):
    image = Image.new('RGB', (W * AA, H * AA), PAPER)
    d = ImageDraw.Draw(image)
    def text(x, y, value, size=24, color=INK, anchor='mm', bold=False):
        d.text((x*AA, y*AA), value, font=font(size, bold), fill=color, anchor=anchor)
    def line(points, color=LINE, width=2):
        d.line([(x*AA, y*AA) for x,y in points], fill=color, width=round(width*AA))
    def rect(box, fill, outline=None, width=1):
        d.rectangle(tuple(v*AA for v in box), fill=fill, outline=outline, width=round(width*AA))
    def arrow(x, y, length, color):
        end = x+length
        line([(x,y),(end,y)],color,3)
        direction = 1 if length > 0 else -1
        d.polygon([(end*AA,y*AA),((end-direction*9)*AA,(y-5)*AA),
                   ((end-direction*9)*AA,(y+5)*AA)], fill=color)

    text(W/2, 28, case.title, 29, bold=True)
    subtitle = f'{case.mass:g} kg' if case.pull == 0 else f'{case.pull:g} N pull · {case.mass:g} kg'
    text(W/2, 66, subtitle, 23, MUTED)
    # A side cutaway of the SAME mesh; hide near walls to reveal the drawer.
    import numpy as np
    from shared_cabinet import mesh, CabinetMesh
    from preview_shared_cabinet import render
    m=mesh(n=12,drawer=sample['q'])
    keep=~np.isin(m.names,['body-left-wall','body-left-frame','drawer-left-wall'])
    m=CabinetMesh(m.triangles[keep],m.colors[keep],m.groups[keep],m.names[keep])
    view=render(m,size=(W,220),eye=(-1,0,0),center=(0,-.89,0),scale=100,ss=AA)
    image.paste(view.resize((W*AA,220*AA)),(0,100*AA))
    d=ImageDraw.Draw(image)
    shift = sample['q'] * 100
    front = 240 + shift
    text(94,306,'Side cutaway',17,MUTED)
    # Label each actual force. Static friction balances the pull while stuck;
    # it is not always equal to the maximum static-friction threshold.
    force = sample['pull']
    if force:
        length = force * 24
        start = front + 33
        arrow(start,157,length,PULL)
        text(start+length/2,118,f'Pull {force:g} N',22,PULL)
    friction = sample['friction']
    if abs(friction) > 1e-9:
        start = front - 54
        length = friction * 24
        arrow(start,196,length,FRICTION)
        text(start+length/2,239,f'Friction {abs(friction):g} N',21,FRICTION)
    for y in range(299,335,7): line([(240,y),(240,y+3)],LINE,1)
    if shift > 1:
        line([(front,296),(front,332)],BLUE_DARK,1)
        arrow(240,322,shift,BLUE_DARK)
    text(W/2,361,f'q = {sample["q"]*100+1e-8:.1f} cm',27,BLUE_DARK)
    phase = 'Pulling' if force else ('Pull removed' if case.pull else 'No pull')
    text(W/2,405,f'{phase} · {sample["t"]:.2f} s',21,MUTED)
    return image.resize((W,H), Image.Resampling.LANCZOS)


def compose(panels, stacked):
    image = Image.new('RGB',(W,H*2) if stacked else (W*2,H),PAPER)
    for i,p in enumerate(panels): image.paste(p,(0,H*i) if stacked else (W*i,0))
    d = ImageDraw.Draw(image)
    d.line((20,H,W-20,H) if stacked else (W,20,W,H-20),fill=LINE,width=1)
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    check()
    if args.check: return
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=dict(model='One-dimensional drawer; chosen teaching values, not measured cabinet properties',
                  pulse_seconds=.5, travel_limit_m=LIMIT, simulation_step_seconds=DT,
                  presentation='Half-speed playback with holds at the start and end; instant reset on replay',
                  examples={})
    for name,pair in PAIRS.items():
        traces=[simulate(c) for c in pair]
        frames=[[panel(c,samples[i]) for c,samples in zip(pair,traces)] for i in range(len(traces[0]))]
        for stacked in (False,True):
            suffix='-stacked' if stacked else ''
            images=[compose(p,stacked) for p in frames]
            strip=Image.new('RGB',(images[0].width*3,images[0].height))
            for i,k in enumerate((0,len(images)//2,-1)): strip.paste(images[k],(i*images[0].width,0))
            palette=strip.quantize(colors=128,method=Image.Quantize.MEDIANCUT)
            indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
            # Match each sampled physics interval at half playback speed.
            durations=[round((traces[0][i+1]['t']-s['t'])*2000) for i,s in enumerate(traces[0][:-1])]+[900]
            durations[0]+=500
            indexed[0].save(OUT/f'{name}{suffix}.gif',save_all=True,append_images=indexed[1:],
                            duration=durations,loop=0,optimize=True,disposal=1)
            images[-1].save(OUT/f'{name}{suffix}.png',optimize=True)
        manifest['examples'][name]=[dict(settings=asdict(c),samples=trace) for c,trace in zip(pair,traces)]
        print(f'{name}: {len(frames)} calculated frames, wide and stacked GIFs',flush=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__ == '__main__': main()
