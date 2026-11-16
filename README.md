# Why Simulation?

A webbook about articulated objects. The first chapter adapts the original ArticulateArena cabinet introduction into a continuous reading layout. The second explains base/world frames, object orientation, meshes, and URDF origins through illustrations of a cabinet and its drawer. The third, **Reading a URDF file**, connects the file structure to the cabinet's parts, shapes, joints, and collision geometry using illustrations redrawn from the cabinet geometry, based on the examples in the supplied AIVC notes.

The fourth chapter, **Changing a URDF**, uses ten newly rendered GIFs to show changes to the drawer axis, a hinge changed into a slide, removal of the drawer, and a swap of the drawer and door shapes. The animations use the cabinet geometry rather than images extracted from the notes.

## Preview locally

Requires Python 3.10 or newer; no packages need to be installed.

```sh
python3 scripts/build_book.py
python3 -m http.server 8769 --bind 127.0.0.1 --directory docs
```

Open [http://127.0.0.1:8769/](http://127.0.0.1:8769/).

## Edit the book

| Location | Purpose |
| --- | --- |
| `book/book.json` | Book title, chapter order, and page names |
| `book/chapters/` | Chapter content as HTML fragments |
| `book/layout.html` | Shared toolbar, contents, search, and footer |
| `book/assets/` | Styles, interactions, fonts, and cabinet media |
| `scripts/build_book.py` | Dependency-free static builder |
| `docs/` | Generated website, ready for GitHub Pages |

Edit the source in `book/`, then rebuild. Keep chapter output files at the root of `docs/` so all pages share the same relative asset paths.

To add a chapter, create an HTML fragment in `book/chapters/` and add its `number`, `title`, `source`, and `output` to `book/book.json`. Use `<header id="chapter-start">` for the chapter heading and `<section id="unique-anchor" data-title="Section name">` with an `<h2>` for each section. The builder generates navigation, search entries, and previous/next chapter links from those files.

The reading controls support a collapsible table of contents, `/` to search, Escape to close search or the mobile menu, and chapter printing. Animations respect reduced-motion preferences. The examples run entirely in the browser.

Figures in the URDF chapter open in an enlarged view without leaving the page. Close that view with its Close button or Escape. All chapter explanations remain expanded in the normal reading layout.

Chapter 4 GIFs autoplay and loop. Static endpoint images replace them for reduced-motion preferences and printing, including in the enlarged view. To regenerate these assets, install the optional authoring dependencies and run:

```sh
python3 -m pip install -r scripts/requirements-animation.txt
python3 scripts/animate_urdf_examples.py
python3 scripts/build_book.py
```

The animation generator checks the changed axes, travel distances, closed-pose alignment after swapping shapes, and the unchanged door motion after removing the drawer. Run only those checks with `python3 scripts/animate_urdf_examples.py --check`. It uses the checked-in geometry snapshot, fixed cameras, and a shared color palette per GIF. The six axis/type examples label the joint's zero-pose reference frame: +X red, +Y green, +Z blue, with the chosen motion axis in purple. These arrows use the same camera projection as the geometry. In this asset the moving joints have zero origin RPY, so their reference directions match the cabinet body frame (+Y up, +Z out of the front); they are not the world-axis convention introduced in Chapter 2. The translucent cabinet reveals the motion; the renderer does not simulate contact or gravity.

## Hosting

The generated website is in `docs/`. To host it with GitHub Pages, configure deployment from the `main` branch and `/docs` folder. All assets use relative paths so the book can be hosted under `/why_simulation/` or a custom domain.

## Sources

- Cabinet media and adapted teaching examples: [ArticulateArena website](https://github.com/YumengHe/ArticulateArena-web), MIT license, copyright 2026 Yumeng He.
- Cabinet origin diagram: projected from the [45168 example geometry](https://github.com/YumengHe/ArticulateArena/tree/11e49256b8e839f04e5da2f481cbea20c54bc2ce/sample_data/45168) in ArticulateArena, following the O/J explanation in the supplied AIVC notes. It shows the drawer at its zero position in the body link's frame.
- URDF chapter figures: original SVG projections of the 45168 geometry, following the examples on pages 14, 18, 25, and 26 of the user-supplied `AIVC.pdf`. Labels and captions are rewritten for beginners. `scripts/data/cabinet-45168.json` stores the source geometry and joint transforms; `python3 scripts/draw_urdf_figures.py` regenerates the five SVGs in `book/assets/figures/`. The drawer is shown at q = 76 cm and the door at q = 90 degrees, their upper position limits. The fixed-joint comparison uses the actual joint_2 rotation and the same Z-up scene/camera in all three panels. Keeping that joint or applying its transform to a new body root gives the same pose; deleting it without replacement does not.
- Chapter 4 animations follow the examples in the six-page user-supplied `AIVC (1).pdf`: drawer axis changes (pages 2–4), swapping geometry and removing the drawer (page 5), and changing the door from revolute to prismatic (pages 5–6). No PDF images or evaluation scores are embedded. The diagonal axis is normalized to unit length. Swapped shapes preserve their original closed placement before following their new joints; the offset cancellation used by the renderer applies to this model's saved coordinates and zero joint rotations, not to every URDF.
- URDF structure and terminology: [ROS-Industrial URDF introduction](https://ros-industrial.github.io/ros2_i_training/_source/urdf/introduction.html). Chapter 3 shows shortened excerpts from the model, with rounded numbers; they are not advertised as a complete simulator-ready model.
- Book layout reference: [Physics-Based Simulation](https://phys-sim-book.github.io/). The layout is independently implemented; its text and source code are not copied.
- Noto Sans: local font copied from ArticulateArena, licensed under the SIL Open Font License; see `book/assets/fonts/OFL.txt`.

The cabinet controls use illustrative motion ranges. They are teaching diagrams, not a rigid-body physics simulator. The drawer's origin diagram uses the closed pose and matching frame orientations of this particular model; opposite offsets are not a universal URDF requirement. The earlier hinged-panel files remain in `book/assets/examples/` for future use, but are not part of the current introductory chapter.
