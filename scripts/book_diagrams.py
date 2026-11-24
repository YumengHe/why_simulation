"""Render the book's responsive diagrams as semantic HTML and small SVG arrows.

Content lives in book/diagrams.json. All labels remain searchable/selectable;
cabinet images are script renders with their own recorded provenance.
"""
from html import escape
import json
import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'book'


def arrow(kind='down'):
    paths = {'down': 'M8 1V23m-5-5 5 5 5-5',
             'fork': 'M500 0V14M250 36V14H750V36m-506-6 6 6 6-6m488 0 6 6 6-6',
             'merge': 'M250 0V14H750V0M500 14V36m-6-6 6 6 6-6',
             'repeat': 'M20 6H9a6 6 0 0 0 0 12h12M14 1l6 5-6 5'}
    view = '0 0 1000 40' if kind in ('fork', 'merge') else '0 0 26 24' if kind == 'repeat' else '0 0 16 24'
    ratio = ' preserveAspectRatio="none"' if kind in ('fork', 'merge') else ''
    return f'<svg class="diagram-arrow diagram-arrow--{kind}" viewBox="{view}"{ratio} aria-hidden="true" focusable="false"><path d="{paths[kind]}"/></svg>'


def card(n, route='', index=None):
    tag = 'a' if n.get('href') else 'div'
    attrs = f' href="{escape(n["href"], quote=True)}"' if tag == 'a' else ''
    classes = 'diagram-card' + (' diagram-card--accent' if n.get('accent') else '')
    out = [f'<{tag} class="{classes}"{attrs}>']
    if route or n.get('label') or index is not None:
        label = n.get('label') or route or f'{index:02d}'
        route_class = ' diagram-card-route' if route and not n.get('label') else ''
        out.append(f'<span class="diagram-card-label{route_class}">{escape(label)}</span>')
    if n.get('title'):
        out.append(f'<strong class="diagram-card-title">{escape(n["title"])}</strong>')
    if n.get('image'):
        out.append(f'<img class="diagram-cabinet" src="{escape(n["image"], quote=True)}" alt="{escape(n.get("alt", ""), quote=True)}" loading="lazy">')
    if n.get('text'):
        out.append(f'<span class="diagram-card-text">{escape(n["text"])}</span>')
    if n.get('body'):
        out.append(f'<div class="diagram-card-text">{n["body"]}</div>')
    if tag == 'a':
        out.append('<span class="diagram-linkmark" aria-hidden="true">↗</span>')
    out.append(f'</{tag}>')
    return ''.join(out)


def flow(nodes, vertical=False):
    cls = ' diagram-flow--vertical' if vertical or len(nodes) > 3 else ''
    return '<ol class="diagram-flow'+cls+'">'+''.join(
        '<li>'+card(n, index=i+1)+(arrow() if i<len(nodes)-1 else '')+'</li>'
        for i,n in enumerate(nodes))+'</ol>'


def render(key, d):
    title_id = 'diagram-'+key+'-title'
    caption_id = 'diagram-'+key+'-caption'
    out = [f'<figure class="book-diagram" id="diagram-{escape(key)}" data-diagram="{escape(key)}" aria-labelledby="{title_id}"'+
           (f' aria-describedby="{caption_id}"' if d.get('caption') else '')+'>',
           '<div class="diagram-panel"><div class="diagram-heading">',
           f'<span class="diagram-kicker">{escape(d.get("kicker", "Workflow"))}</span>',
           f'<h3 id="{title_id}">{escape(d["title"])}</h3>']
    if d.get('intro'):
        out.append(f'<p>{escape(d["intro"])}</p>')
    out.append('</div>')
    kind = d.get('kind', 'flow')
    if kind == 'flow':
        out.append(flow(d['nodes'], d.get('vertical', False)))
    elif kind == 'lanes':
        routes = d['routes']
        if d.get('input'):
            out.append('<div class="diagram-shared">'+card(d['input'])+arrow('fork')+'</div>')
        out.append('<div class="diagram-lanes"><span class="diagram-lane-spacer" aria-hidden="true"></span>')
        for route in routes:
            out.append(f'<strong class="diagram-lane-name">{escape(route)}</strong>')
        for i,row in enumerate(d['rows']):
            if i:
                out.append('<span class="diagram-lane-spacer" aria-hidden="true"></span>')
                out.extend('<div class="diagram-lane-arrow">'+arrow()+'</div>' for _ in routes)
            out.append(f'<div class="diagram-role"><span>{i+1:02d}</span><strong>{escape(row["title"])}</strong></div>')
            for route,n in zip(routes,row['nodes']):
                out.append(card(n, route))
        out.append('</div>')
        if d.get('output'):
            out.append('<div class="diagram-shared">'+arrow('merge')+card(d['output'])+'</div>')
        if d.get('after'):
            out.append('<div class="diagram-after">'+flow(d['after'])+'</div>')
    elif kind == 'groups':
        out.append('<div class="diagram-groups">')
        for group in d['groups']:
            out.append('<div class="diagram-group"><h4>'+escape(group['title'])+'</h4>')
            out.extend(card(n) for n in group['nodes'])
            out.append('</div>')
        out.append('</div>')
    elif kind == 'tree':
        out.append('<div class="diagram-structure"><img class="diagram-cabinet" src="'+escape(d['image'])+'" alt="'+escape(d['alt'])+'" loading="lazy"><div class="diagram-tree">'+card(d['root'])+arrow('fork')+'<div class="diagram-tree-children">')
        out.extend(card(n) for n in d['children'])
        out.append('</div></div></div>')
    elif kind == 'task':
        out.append('<div class="diagram-task"><img class="diagram-cabinet" src="'+escape(d['image'])+'" alt="'+escape(d['alt'])+'" loading="lazy"><div>'+card(d['criterion'])+'<div class="diagram-range" role="img" aria-label="Success threshold: 90 percent of the opening range"><span></span></div><div class="diagram-range-labels"><span>Closed</span><strong>90% threshold</strong><span>Fully open</span></div></div></div>')
        out.append(flow(d['nodes']))
    else:
        raise ValueError(f'Unknown diagram type: {kind}')
    if d.get('repeat'):
        out.append('<p class="diagram-feedback">'+arrow('repeat')+'<span>'+d['repeat']+'</span></p>')
    if d.get('note'):
        out.append('<p class="diagram-note">'+d['note']+'</p>')
    out.append('</div>')
    if d.get('caption'):
        out.append(f'<figcaption id="{caption_id}">'+d['caption']+'</figcaption>')
    return ''.join(out)+'</figure>'


def expand_diagrams(content):
    definitions = json.loads((SOURCE/'diagrams.json').read_text())
    return re.sub(r'\{\{diagram:([\w-]+)\}\}', lambda m: render(m[1], definitions[m[1]]), content)
