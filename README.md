# Why Simulation?

A webbook about articulated objects. The first chapter adapts the original ArticulateArena cabinet introduction into a continuous reading layout. The second explains base/world frames, object orientation, meshes, and URDF origins through illustrations of a cabinet and its drawer. The third, **Reading a URDF file**, connects the file structure to the cabinet's parts, shapes, joints, and collision geometry using illustrations redrawn from the cabinet geometry, based on the examples in the supplied AIVC notes.

The fourth chapter, **Changing a URDF**, uses ten newly rendered GIFs to show changes to the drawer axis, a hinge changed into a slide, removal of the drawer, and a swap of the drawer and door shapes. The animations use the cabinet geometry rather than images extracted from the notes.

The fifth chapter, **From animation to simulation**, compares a box following chosen positions with a box falling under gravity. Readers can change the table height and switch gravity off, then connect the difference to the drawer's opening distance, `q`.

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

Chapter 5 uses an original browser demonstration in `book/assets/physics-demo.js`: one-dimensional motion integrated with semi-implicit Euler at 240 steps per second, with a static tabletop and perfectly inelastic contact. There is no air resistance, bounce, or rotational motion. The comparison autoplays; reduced-motion preferences show settled results instead. The demo uses no external physics engine. Optional per-chapter JavaScript files are listed under `scripts` in `book/book.json`.

The same chapter adds four original paired drawer GIFs: different pulls, different masses, different rail friction, and motion after release. `scripts/animate_drawer_forces.py` calculates one-dimensional dynamics from illustrative properties, then draws side views. It uses exact constant-acceleration updates over 1 ms segments, resolves stopping under Coulomb friction, and includes inelastic travel stops at 0 and 0.76 m. Static friction balances forces up to its threshold; it is not always equal to that threshold. The geometry is a teaching diagram, not measured cabinet geometry. This model does not run a full 3D contact simulation.

Regenerate the force examples with `python3 scripts/animate_drawer_forces.py` after installing the optional animation dependencies below. Run `python3 scripts/animate_drawer_forces.py --check` to check independent analytic results for acceleration, coasting, stopping distance, sticking, and travel limits. Numerical traces and settings are saved in `book/assets/forces/manifest.json`. Wide and stacked GIFs keep each comparison synchronized on desktop and mobile; PNG end states support reduced motion and printing. Playback is half speed, with holds at the first and last frame before the experiment resets.

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
- Chapter 5 physics explanations: OpenStax University Physics Volume 1, [Newton’s first law](https://openstax.org/books/university-physics-volume-1/pages/5-2-newtons-first-law), [Newton’s second law](https://openstax.org/books/university-physics-volume-1/pages/5-3-newtons-second-law), and [friction](https://openstax.org/books/university-physics-volume-1/pages/6-2-friction). The drawings and simulations are original; source figures are not copied.
- Book layout reference: [Physics-Based Simulation](https://phys-sim-book.github.io/). The layout is independently implemented; its text and source code are not copied.
- Noto Sans: local font copied from ArticulateArena, licensed under the SIL Open Font License; see `book/assets/fonts/OFL.txt`.

The cabinet controls use illustrative motion ranges. They are teaching diagrams, not a rigid-body physics simulator. The drawer's origin diagram uses the closed pose and matching frame orientations of this particular model; opposite offsets are not a universal URDF requirement. The earlier hinged-panel files remain in `book/assets/examples/` for future use, but are not part of the current introductory chapter.
