# Media sources and regeneration

Embedded illustrations and videos are drawn from explicit geometry, numeric
examples, or vector code, or are screenshots supplied by the author. Screenshot
preparation uses explicit crops, resizing, and annotation. No text-to-image,
image-to-image, or generative-video model supplies the finished media. AI
assistance with writing drawing code or layout is compatible with this policy.

The complete per-file source mapping and SHA-256 hashes are in
[`scripts/media-inventory.json`](scripts/media-inventory.json). Verify the
reviewed files with `python3 scripts/audit_media.py`. After intentionally changing
media, review its source before updating the inventory with `--write`.

| Media | Drawing or rendering source |
| --- | --- |
| Shared cabinet and preview | `scripts/shared_cabinet.py`, `scripts/preview_shared_cabinet.py`; deterministic closed primitives, fixed handles, OBJ/URDF exports, geometry validation. |
| Chapter 2 classification and workflow maps | `scripts/draw_chapter2_maps.py`; explicit SVG boxes, arrows, and labels. Field meaning and storage are shown as combinable choices; the feedback path applies to 3DGS/NeRF fitting. |
| Blender modeling, camera, and render screenshots | `scripts/prepare_blender_figures.py`; crops and leader labels from the eight author-supplied originals in `scripts/data/blender-screenshots/`. Original pixels are retained apart from crop/resampling; each input hash is recorded in the inventory. |
| Shared Blender/Maya rig, keyframe, and curve teaching diagrams | `scripts/draw_maya_examples.py`; explicit vector geometry, a planar two-link IK solution, and linear/cubic drawer-position curves. The legacy `assets/maya/` paths are retained. These illustrate animation controls shared by both applications, not interface screenshots or physics simulation outputs. |
| Box falling onto a cabinet shelf | `scripts/render_blender_physics.py`; scripted box geometry, Blender's Bullet rigid-body physics, and Cycles rendering. Only the initial box pose is supplied; later positions are computed from gravity and collisions. Parameters and sampled poses are recorded in `book/assets/software-physics/manifest.json`. |
| Introductory cabinet video and poster | `scripts/animate_cabinet_intro.py`; triangles from `scripts/shared_cabinet.py`, per-pixel depth buffering, prescribed drawer/door joint positions |
| Mesh/Gaussian cabinet comparison | `scripts/render_cabinet_comparison.py`; shared cabinet primitives, triangle rasterization, and perspective Gaussian splatting |
| Cabinet points, meshes, Gaussian and field diagrams | `scripts/draw_representation_overview.py` |
| Cabinet voxel grid | `scripts/draw_voxel_cabinet.py`; center-sampled occupancy of the shared cabinet in 4 cm cells, drawing exposed occupied-cell faces. |
| One Gaussian, twelve neighbours, and the whole cabinet | `scripts/draw_gaussian_groups.py`; one actual sample and its neighbours from the shared 4,748-Gaussian cabinet, with two-standard-deviation shape guides and a rendered whole view. |
| Basic representation and mesh diagrams | `scripts/draw_representation_diagrams.py`, `scripts/draw_representation_examples.py`, `scripts/draw_reconstruction_story.py` |
| Low/high polygon cabinet comparison | `scripts/draw_cabinet_mesh_detail.py`; exact triangle counts and a depth buffer |
| Two-blob projection video and stills | `scripts/animate_projection.py`; camera projection and covariance calculations |
| Cabinet projection video and stills | `scripts/animate_gaussian_cabinet.py`; fixed analytic Gaussian scene, projected and blended per camera |
| Cabinet opacity slider images | `scripts/draw_cabinet_opacity.py`; the same scene re-rendered at different opacities |
| Camera matching and Gaussian fitting illustrations | `scripts/draw_gaussian_learning.py`; constructed teaching stages and geometrically consistent camera rays |
| NeRF cabinet illustrations | `scripts/draw_nerf_cabinet.py`; an analytic color/density field and numerical volume rendering |
| URDF cabinet figures and motion GIFs | `scripts/draw_urdf_figures.py`, `scripts/animate_urdf_examples.py`; the shared cabinet via `scripts/cabinet_legacy.py` and joint transforms |
| Force, mass, friction, release GIFs | `scripts/animate_drawer_forces.py`; calculated one-dimensional motion |
| Collision preparation cutaways | `scripts/draw_simulation_workflow.py`; shared cabinet geometry, simplified contact boxes, and geometric clearance checks |
| VLA before/after illustrations | `scripts/draw_vla_flow.py`; vector drawing and arm inverse kinematics |
| Origin, panel, and drawer SVGs | `scripts/draw_cabinet_frames.py`, using the shared cabinet geometry |
| Interactive in-page diagrams | `book/assets/articulation.js`, `frames.js`, `physics-demo.js`, `representation-demo.js`, and inline SVG/HTML in `book/chapters/` |

All cabinet examples now derive their panels, tray, and fixed handles from
`scripts/shared_cabinet.py`: 21 box components and six capped handle cylinders.
The body has a closed top and back. The drawer is an open tray; the lower door
hinges on its left edge. The two handles belong to their owning parts. The
6-sided and 32-sided handle versions have 396 and 1,020 triangles respectively.
`preview_shared_cabinet.py` checks and exports the model; `cabinet_legacy.py`
expresses the same geometry in the existing URDF lesson's coordinate frame.
Normal views use opaque surfaces. Cutaways, diagnostic overlays and opacity
experiments are intentional, identified teaching views of the same model.

The old ArticulateArena 45168 snapshot remains only as a historical source,
not the geometry rendered by the current book. Source credits are retained.
The downloadable teaching URDF and component OBJ files match the current
illustrations; shortened code excerpts use its origins and file names.

The Blender screenshots were supplied for inclusion on 2026-11-22. The orange
rectangle in the modeling screenshot is a selected image Empty used as a 2D
reference, not a camera frame. Four additional screenshots supplied the same day
show two camera setups and their view previews, paired in the order provided by
the author. Labels identify the selected camera wireframes; no camera rays or
geometry are invented in the screenshots. Previews retain the editor's overlays
and are distinguished from final render results. The virtual-camera workflow
uses schematic inline SVG icons and HTML labels. The viewport and grayscale
result are two crops of the same screenshot; the colored render is a separate
supplied image, not a render reproduced from a `.blend` file by this repository.

## What the examples establish

The Gaussian/NeRF figures explain the rendering and fitting workflow. Their
early/later stages are constructed examples, not recorded training runs. The
new representation comparison is not a TRELLIS prediction. The book links to
the original projects for actual learned-model results.

The force GIFs calculate motion from a simplified dynamics model. URDF GIFs and
the introductory video use prescribed joint positions; they do not simulate
contact. These distinctions are recorded alongside each generator.

The software-page shelf example is an actual Blender rigid-body simulation.
It uses the shared cabinet with its lower door open, separate passive component colliders,
and one active 1 kg box with no position keyframes. Its three camera images
are Cycles renders at 0, 0.2, and 0.6 seconds. To regenerate them, run
`blender --background --factory-startup --python scripts/render_blender_physics.py`.

## Rebuild media

Install the authoring dependencies from `scripts/requirements-animation.txt`
in a Python environment. Cabinet generators use NumPy and Pillow; some other SVG generators use only
the standard library. The static book itself has
no package dependencies. MP4 encoding requires an installed FFmpeg executable.

```sh
python3 scripts/preview_shared_cabinet.py
python3 scripts/cabinet_legacy.py
python3 scripts/draw_cabinet_frames.py
python3 scripts/draw_chapter2_maps.py
python3 scripts/render_cabinet_comparison.py
python3 scripts/prepare_blender_figures.py
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
locally reproducible render of the shared teaching cabinet.
