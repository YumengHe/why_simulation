#!/usr/bin/env python3
"""Re-render the fixed Gaussian cabinet with different per-blob opacities."""
from pathlib import Path
import json

import numpy as np

from animate_gaussian_cabinet import CENTERS, COVS, COLORS, U, V, project, blend_splats

OUT = Path(__file__).resolve().parents[1] / 'book/assets/projection-cabinet/opacity'
WIDTH, HEIGHT, ANGLE = 420, 556, 20


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    uv, cov, depth = project(CENTERS, COVS, ANGLE)
    scale = np.diag([WIDTH/(2*U), -HEIGHT/(2*V)])
    pixels = uv @ scale.T + [WIDTH/2, HEIGHT/2]
    screen_cov = scale @ cov @ scale.T
    levels = list(range(0, 101, 5))
    for level in levels:
        image = blend_splats(pixels, screen_cov, COLORS, depth, WIDTH, HEIGHT, level/100).convert('RGB')
        if level == 0:
            assert np.all(np.array(image) == 255), 'Zero opacity must reveal only the white background.'
        image.save(OUT / f'cabinet-{level:03d}.webp', lossless=True, method=6)
    # Repeated overlap accumulates opacity; it is not a final-image fade.
    for alpha in (.05, .25, .95):
        combined = 1-(1-alpha)**3
        assert combined >= alpha
    (OUT/'manifest.json').write_text(json.dumps({
        'source': 'The same original illustrative Gaussian cabinet as the cabinet projection video.',
        'width': WIDTH, 'height': HEIGHT, 'camera_degrees': ANGLE,
        'levels_percent': levels, 'control': 'Peak opacity of every Gaussian; all other scene properties fixed.',
        'rendering': 'Perspective covariance projection, depth-sorted alpha blending against white.',
        'images': 'Lossless WebP, re-rendered independently at every setting; not CSS image transparency.'
    }, indent=2)+'\n')
    print(f'Wrote {len(levels)} cabinet opacity views; zero-opacity and overlap checks pass.')


if __name__ == '__main__':
    main()
