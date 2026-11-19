# Media sources and regeneration

All embedded illustrations and videos are drawn from explicit geometry, numeric
examples, or vector code. No text-to-image, image-to-image, or generative-video
model supplies the finished media. AI assistance with writing drawing code or
layout is compatible with this policy.

The complete per-file source mapping and SHA-256 hashes are in
[`scripts/media-inventory.json`](scripts/media-inventory.json). Verify the
reviewed files with `python3 scripts/audit_media.py`. After intentionally changing
media, review its source before updating the inventory with `--write`.

| Media | Drawing or rendering source |
| --- | --- |
| Introductory cabinet video and poster | `scripts/animate_cabinet_intro.py`; triangles from `scripts/data/cabinet-45168.json`, prescribed drawer/door joint positions |
| Mesh/Gaussian cabinet comparison | `scripts/render_cabinet_comparison.py`; explicit cabinet boxes, triangle rasterization, and perspective Gaussian splatting |
| Cabinet points, meshes, Gaussian and field diagrams | `scripts/draw_representation_overview.py` |
| Basic representation and mesh diagrams | `scripts/draw_representation_diagrams.py`, `scripts/draw_representation_examples.py`, `scripts/draw_reconstruction_story.py` |
| Low/high polygon cabinet comparison | `scripts/draw_cabinet_mesh_detail.py`; exact triangle counts and a depth buffer |
| Two-blob projection video and stills | `scripts/animate_projection.py`; camera projection and covariance calculations |
| Cabinet projection video and stills | `scripts/animate_gaussian_cabinet.py`; fixed analytic Gaussian scene, projected and blended per camera |
| Cabinet opacity slider images | `scripts/draw_cabinet_opacity.py`; the same scene re-rendered at different opacities |
| Camera matching and Gaussian fitting illustrations | `scripts/draw_gaussian_learning.py`; constructed teaching stages and geometrically consistent camera rays |
| NeRF cabinet illustrations | `scripts/draw_nerf_cabinet.py`; an analytic color/density field and numerical volume rendering |
| URDF cabinet figures and motion GIFs | `scripts/draw_urdf_figures.py`, `scripts/animate_urdf_examples.py`; the checked-in cabinet geometry and joint transforms |
| Force, mass, friction, release GIFs | `scripts/animate_drawer_forces.py`; calculated one-dimensional motion |
| Collision preparation cutaways | `scripts/draw_simulation_workflow.py`; explicit boxes and geometric clearance checks |
| VLA before/after illustrations | `scripts/draw_vla_flow.py`; vector drawing and arm inverse kinematics |
| Standalone origin, panel, drawer, and favicon SVGs | Editable vector primitives in their `.svg` source files; no embedded raster image |
| Interactive in-page diagrams | `book/assets/articulation.js`, `frames.js`, `physics-demo.js`, `representation-demo.js`, and inline SVG/HTML in `book/chapters/` |

The cabinet geometry snapshot comes from ArticulateArena sample 45168 at commit
`11e49256b8e839f04e5da2f481cbea20c54bc2ce`; its source is also recorded in the JSON.
The project’s source credits remain in the README. The geometry is an existing
3D model, not a photograph copied from the supplied PDF.

## What the examples establish

The Gaussian/NeRF figures explain the rendering and fitting workflow. Their
early/later stages are constructed examples, not recorded training runs. The
new representation comparison is not a TRELLIS prediction. The book links to
the original projects for actual learned-model results.

The force GIFs calculate motion from a simplified dynamics model. URDF GIFs and
the introductory video use prescribed joint positions; they do not simulate
contact. These distinctions are recorded alongside each generator.

## Rebuild media

Install the authoring dependencies from `scripts/requirements-animation.txt`
in a Python environment. Static SVG generators use only the standard library;
raster and animation scripts use NumPy and Pillow. The static book itself has
no package dependencies. MP4 encoding requires an installed FFmpeg executable.

```sh
python3 scripts/render_cabinet_comparison.py
python3 scripts/animate_cabinet_intro.py --ffmpeg /path/to/ffmpeg
python3 scripts/animate_projection.py --ffmpeg /path/to/ffmpeg
python3 scripts/animate_gaussian_cabinet.py --ffmpeg /path/to/ffmpeg
python3 scripts/audit_media.py --write
python3 scripts/build_book.py
```

Run the other listed scripts by filename to regenerate their assets. Projection
scripts also accept `--stills` and `--check`. URDF and force animation scripts
accept `--check`. Font rendering or encoder versions can alter byte hashes even
when the underlying scene is unchanged.

## Replaced material

The former TRELLIS toolbox gallery images were removed from both source assets
and the generated website. Their input image was made with DALL·E 3. Section
2.7 now uses independently scripted cabinet views and links to the external
gallery. The imported introductory cabinet video has also been replaced by a
locally reproducible render of the checked-in geometry.
