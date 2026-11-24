#!/usr/bin/env python3
"""Scripted cabinet stages and method diagrams; no model inference.

The cabinet geometry, cameras and colors are explicitly authored. Gray and
colored stages share identical triangles. Surface colors stand in for a
textured appearance; they are not a texture map produced by Hunyuan3D-Paint.
"""
from pathlib import Path
from html import escape
import json
import numpy as np
from shared_cabinet import mesh, CabinetMesh, validate
from preview_shared_cabinet import render

OUT = Path(__file__).resolve().parents[1] / 'book/assets/generation-methods'
INK, MUTED, TEAL, GOLD = '#293632', '#5f6862', '#528b82', '#a67a20'


def diagram(mobile=False):
    w, h = (480, 1100) if mobile else (960, 680)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
             '<title>Hunyuan3D 2.0 and original TRELLIS: two generation pipelines</title>',
             '<desc>Starting with a cabinet picture, Hunyuan3D creates a mesh and adds a texture. TRELLIS chooses locations near the surfaces, describes shape and appearance there, and converts its internal description into a mesh, Gaussians, or a radiance field.</desc>',
             '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 1L9 5L0 9" fill="none" stroke="#64736c" stroke-width="1.5"/></marker></defs>',
             f'<rect width="{w}" height="{h}" fill="#fffefa"/>']

    def text(x, y, lines, size=22, color=INK, bold=False, anchor='start'):
        if isinstance(lines, str): lines = [lines]
        for i, line in enumerate(lines):
            parts.append(f'<text x="{x}" y="{y+i*29}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{600 if bold else 400}" fill="{color}" text-anchor="{anchor}">{escape(line)}</text>')

    def box(x, y, bw, bh, title, subtitle, color):
        parts.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="6" fill="white" stroke="{color}" stroke-width="1.5"/>')
        text(x+bw/2, y+32, title, 23, color, True, 'middle')
        text(x+bw/2, y+64, subtitle, 20, MUTED, anchor='middle')

    def arrow(path):
        parts.append(f'<path d="{path}" fill="none" stroke="#64736c" stroke-width="2" marker-end="url(#arrow)"/>')

    text(28, 40, 'From a cabinet picture', 28, bold=True)
    text(28, 75, 'Follow the shape and appearance.', 21, MUTED)
    if mobile:
        text(28, 125, 'Hunyuan3D 2.0', 25, TEAL, True)
        box(40, 150, 400, 98, 'Create the shape', 'Cabinet panels and raised handles', TEAL)
        arrow('M240 248V287')
        box(40, 296, 400, 98, 'Add a texture', 'Colors guided by the picture', TEAL)
        arrow('M240 394V429')
        box(40, 438, 400, 90, 'Textured mesh', 'Surface shape with its appearance', TEAL)
        text(28, 594, 'Original TRELLIS', 25, GOLD, True)
        box(40, 620, 400, 98, 'Choose 3D locations', 'Where to describe the surfaces', GOLD)
        arrow('M240 718V757')
        box(40, 766, 400, 98, 'Describe the cabinet', 'Shape and appearance at these locations', GOLD)
        arrow('M240 864V903')
        box(40, 912, 400, 98, 'Choose an output', 'Mesh / Gaussians / radiance field', GOLD)
        text(28, 1060, 'Convert the internal description to 3D data.', 19, MUTED)
    else:
        text(28, 134, 'Hunyuan3D 2.0', 26, TEAL, True)
        box(28, 164, 280, 114, 'Create the shape', ['Cabinet panels', 'and raised handles'], TEAL)
        arrow('M309 220H333')
        box(340, 164, 280, 114, 'Add a texture', ['Colors and patterns', 'guided by the picture'], TEAL)
        arrow('M621 220H645')
        box(652, 164, 280, 114, 'Textured mesh', ['Surface shape', 'with its appearance'], TEAL)
        text(28, 350, 'Original TRELLIS', 26, GOLD, True)
        box(28, 380, 280, 114, 'Choose 3D locations', ['Where to describe', 'the cabinet’s surfaces'], GOLD)
        arrow('M309 436H333')
        box(340, 380, 280, 114, 'Describe the cabinet', ['Shape and appearance', 'around those locations'], GOLD)
        arrow('M621 436H645')
        box(652, 380, 280, 114, 'Choose an output', ['Convert the internal', 'description'], GOLD)
        arrow('M792 494V529')
        text(792, 558, ['Mesh / Gaussians /', 'radiance field'], 23, GOLD, True, 'middle')
        text(28, 644, 'Generation steps and outputs · the examples use the same cabinet picture.', 21, MUTED)
    parts.append('</svg>')
    (OUT / ('pipelines-mobile.svg' if mobile else 'pipelines.svg')).write_text('\n'.join(parts)+'\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    validate(32)
    model = mesh(n=32)
    gray = CabinetMesh(model.triangles.copy(), np.full_like(model.colors, 190),
                       model.groups.copy(), model.names.copy())
    assert np.array_equal(gray.triangles, model.triangles)
    # Identical camera, geometry, framing and lighting for shape/appearance.
    settings = dict(size=(600, 600), center=(0, -.13, 0), scale=245, ss=3)
    render(model, eye=(0, -1, .03), **settings).save(OUT/'input.png')
    render(gray, eye=(3, -6, 2.6), **settings).save(OUT/'shape.png')
    render(model, eye=(3, -6, 2.6), **settings).save(OUT/'appearance.png')
    diagram(); diagram(mobile=True)
    (OUT/'manifest.json').write_text(json.dumps({
        'generator': 'scripts/draw_generation_methods.py',
        'geometry': 'scripts/shared_cabinet.py',
        'renderer': 'scripts/preview_shared_cabinet.py; opaque depth-tested triangles',
        'meaning': 'Illustrations of the inputs and outputs of the two stages, not model predictions.',
        'appearance': 'Authored surface colors illustrate where a generated texture would supply appearance; no texture generation is run.',
        'comparison': 'Shape and appearance panels share the same triangles, camera, lighting and framing.',
        'method_scope': 'Hunyuan3D 2.0 and original TRELLIS only.',
        'sources': ['https://arxiv.org/abs/2501.12202', 'https://arxiv.org/abs/2412.01506']
    }, indent=2)+'\n')
    print('Rendered three canonical cabinet stages and two responsive method diagrams.')


if __name__ == '__main__': main()
