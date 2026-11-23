#!/usr/bin/env python3
"""Sample the shared cabinet into occupied grid cells and draw exposed faces."""
from pathlib import Path
import json
import numpy as np
from shared_cabinet import field
from draw_representation_overview import raster

OUT = Path(__file__).resolve().parents[1]/'book/assets/diagrams'
CELL = .04
ORIGIN = np.array([-.70, -.74, -.90])
SHAPE = (35, 30, 45)


def main():
    indices = np.indices(SHAPE).reshape(3,-1).T
    centers = ORIGIN + (indices + .5)*CELL
    density, colors = field(centers, edge=.001)
    occupied = (density > 40).reshape(SHAPE)
    colors = (colors*255).reshape(SHAPE+(3,))
    faces = []
    for index in np.argwhere(occupied):
        lo = ORIGIN+index*CELL
        hi = lo+CELL
        center = (lo+hi)/2
        for axis in range(3):
            other = [a for a in range(3) if a != axis]
            for side in (-1,1):
                neighbour = index.copy(); neighbour[axis] += side
                if np.all(neighbour >= 0) and np.all(neighbour < SHAPE) and occupied[tuple(neighbour)]:
                    continue
                quad = []
                for a,b in ((0,0),(1,0),(1,1),(0,1)):
                    point = lo.copy()
                    point[axis] = hi[axis] if side > 0 else lo[axis]
                    point[other[0]] += a*CELL
                    point[other[1]] += b*CELL
                    quad.append(point)
                quad = np.array(quad)
                if np.cross(quad[1]-quad[0],quad[2]-quad[0]) @ (quad.mean(axis=0)-center) < 0:
                    quad = quad[::-1]
                faces.append((quad,colors[tuple(index)]))
    assert len(faces) and occupied.any() and not occupied.all()
    im,_ = raster('quads', faces)
    im.save(OUT/'cabinet-representation-voxels.png')
    (OUT/'cabinet-voxels.json').write_text(json.dumps({
        'source':'scripts/shared_cabinet.py', 'cell_size_m':CELL,
        'grid_shape':SHAPE,'occupied_cells':int(occupied.sum()),
        'rule':'A cell is occupied when its center lies inside the shared cabinet geometry.',
        'display':'Only exposed faces of occupied cells; empty cells are left unfilled.'
    },indent=2)+'\n')
    print(f'Voxel cabinet: {occupied.sum()} occupied cells, {len(faces)} exposed faces.')


if __name__ == '__main__':
    main()
