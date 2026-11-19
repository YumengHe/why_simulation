#!/usr/bin/env python3
"""Inventory book media and verify recorded source paths and file hashes.

The inventory records an author-reviewed source mapping. It is not an AI-image
detector; hashes detect changes after that review. Register new raster/video
assets explicitly rather than silently assigning them a generic provenance.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'book/assets'
MANIFEST=ROOT/'scripts/media-inventory.json'
SUFFIXES={'.svg','.png','.jpg','.jpeg','.webp','.gif','.mp4','.webm'}
DIRECTORIES={
    'experiments':'animate_urdf_examples.py',
    'figures':'draw_urdf_figures.py',
    'forces':'animate_drawer_forces.py',
    'gaussian-learning':'draw_gaussian_learning.py',
    'media':'animate_cabinet_intro.py',
    'nerf-cabinet':'draw_nerf_cabinet.py',
    'projection':'animate_projection.py',
    'projection-cabinet':'animate_gaussian_cabinet.py',
    'projection-cabinet/opacity':'draw_cabinet_opacity.py',
    'simulation-workflow':'draw_simulation_workflow.py',
    'examples/cabinet-representations':'render_cabinet_comparison.py',
}
DIAGRAM_SCRIPTS={
    'draw_reconstruction_story.py':{'handle-coarse','handle-fine','cylinder-mesh-coarse','cylinder-mesh-fine',
        'cabinet-wireframe','cabinet-rendered','gaussian-projection-side','gaussian-projected-image',
        'nerf-query-example','handle-painted','handle-raised'},
    'draw_representation_examples.py':{'mesh-parts','mesh-one-quad','mesh-two-triangles',
        'gaussian-opacity-low','gaussian-opacity-high','nerf-ray-example','collision-filled','collision-hollow'},
    'draw_representation_diagrams.py':{'representation-points','representation-triangles',
        'representation-quads','representation-gaussians','representation-nerf'},
    'draw_representation_overview.py':{'cabinet-representation-'+m for m in ('points','quads','triangles','gaussians','field')},
    'draw_cabinet_mesh_detail.py':{'cabinet-mesh-coarse','cabinet-mesh-fine'},
    'draw_vla_flow.py':{'vla-drawer-before','vla-drawer-after'},
}
# These files are themselves editable vector drawing programs, not raster images.
VECTOR_SOURCES={'favicon.svg','diagrams/cabinet-origins.svg','diagrams/drawer-shapes.svg',
                'diagrams/side-panel-shape.svg','diagrams/side-panel-mesh.svg'}


def inventory():
    entries=[]
    for path in sorted(ASSETS.rglob('*')):
        if path.suffix.lower() not in SUFFIXES:
            continue
        relative=path.relative_to(ASSETS).as_posix()
        if relative in VECTOR_SOURCES:
            source=path.relative_to(ROOT).as_posix(); kind='editable-vector-source'
        else:
            script=DIRECTORIES.get(path.parent.relative_to(ASSETS).as_posix())
            if path.parent==ASSETS/'diagrams':
                script=next((s for s,names in DIAGRAM_SCRIPTS.items() if path.stem in names),None)
            if not script:
                raise ValueError(f'Unreviewed media source: {relative}')
            source='scripts/'+script;kind='script-rendered'
        assert (ROOT/source).is_file(),f'Missing generator: {source}'
        if path.suffix=='.svg':
            root=ET.parse(path).getroot()
            for element in root.iter():
                assert element.tag.rsplit('}',1)[-1] not in {'image','foreignObject'},f'Embedded non-vector content: {relative}'
        entries.append({'asset':'book/assets/'+relative,'source':source,'kind':kind,
                        'sha256':sha256(path.read_bytes()).hexdigest()})
    return {'policy':'Script-rendered media and editable vector drawings; no direct generative-image or generative-video assets.',
            'scope':'All image/video files under book/assets, including unused retained figures.',
            'entries':entries}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true')
    args=parser.parse_args(); data=inventory()
    if args.write:
        MANIFEST.write_text(json.dumps(data,indent=2)+'\n')
    else:
        expected=json.loads(MANIFEST.read_text())
        if expected!=data:
            raise SystemExit('Media changed since the source audit. Review sources and update the inventory with --write.')
    entries=data['entries']
    print(f"Verified {len(entries)} media files: {sum(e['kind']=='script-rendered' for e in entries)} script renders and {sum(e['kind']=='editable-vector-source' for e in entries)} vector sources.")


if __name__=='__main__':main()
