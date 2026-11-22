#!/usr/bin/env python3
"""Run inside Blender: simulate a rigid box falling onto a cabinet shelf.

blender --background --factory-startup --python scripts/render_blender_physics.py

The only box pose supplied is its initial pose. Bullet computes later poses.
Cycles renders selected frames. No animation keyframes or generative images.
"""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'book/assets/software-physics'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 560
scene.render.resolution_y = 620
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.fps = 60
scene.frame_start, scene.frame_end = 1, 61
scene.gravity = (0, 0, -9.81)
scene.world.color = (.6, .6, .6)
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.83, .86, .9, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .5
scene.view_settings.view_transform = 'AgX'


def mat(name, rgba):
    material = bpy.data.materials.new(name)
    material.diffuse_color = rgba
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = rgba
    bsdf.inputs['Roughness'].default_value = .65
    return material


teal = mat('Cabinet teal', (.21, .39, .35, 1))
inside = mat('Shelf light wood', (.72, .67, .51, 1))
blue = mat('Drawer blue', (.13, .32, .49, 1))
orange = mat('Falling box gold', (.82, .39, .06, 1))
paper = mat('Ground', (.89, .88, .84, 1))
handle = mat('Handle', (.75, .78, .72, 1))


def box(name, center, size, material, rigid=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if rigid:
        bpy.ops.rigidbody.object_add()
        obj.rigid_body.type = rigid
        obj.rigid_body.collision_shape = 'BOX'
        obj.rigid_body.use_margin = True
        obj.rigid_body.collision_margin = .001
        obj.rigid_body.friction = .6
        obj.rigid_body.restitution = 0
    bevel = obj.modifiers.new('Small visible edge bevel', 'BEVEL')
    bevel.width, bevel.segments = .008, 3
    obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return obj


box('Cabinet left wall', (-.58, 0, .77), (.08, .78, 1.42), teal, 'PASSIVE')
box('Cabinet right wall', (.58, 0, .77), (.08, .78, 1.42), teal, 'PASSIVE')
box('Cabinet back', (0, .36, .77), (1.08, .06, 1.42), teal, 'PASSIVE')
box('Cabinet bottom', (0, 0, .10), (1.16, .78, .08), teal, 'PASSIVE')
shelf_top = .58
box('Shelf', (0, 0, shelf_top-.04), (1.08, .74, .08), inside, 'PASSIVE')
box('Drawer below shelf', (0, -.39, .33), (1.03, .07, .30), blue, 'PASSIVE')
box('Handle support left', (-.18, -.445, .35), (.035, .07, .035), handle)
box('Handle support right', (.18, -.445, .35), (.035, .07, .035), handle)
box('Drawer handle', (0, -.485, .35), (.39, .035, .035), handle)
box('Floor', (0, 0, -.025), (200, 200, .05), paper, 'PASSIVE')
falling = box('Falling box', (0, -.09, 1.18), (.25, .25, .25), orange, 'ACTIVE')
falling.rigid_body.mass = 1
falling.rigid_body.linear_damping = 0
falling.rigid_body.angular_damping = .05
world = scene.rigidbody_world
world.substeps_per_frame = 10
world.solver_iterations = 30
world.point_cache.frame_start = scene.frame_start
world.point_cache.frame_end = scene.frame_end

bpy.ops.object.camera_add(location=(2.5, -5, 2.45))
camera = bpy.context.object
camera.name = 'Render camera'
camera.rotation_euler = (Vector((0, -.02, .76))-camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1.93
scene.camera = camera
for name, position, power, size in (
    ('Key light', (0, -3.5, 5), 450, 4),
    ('Fill light', (-3, -1, 2), 200, 3),
):
    bpy.ops.object.light_add(type='AREA', location=position)
    lamp = bpy.context.object
    lamp.name = name
    lamp.data.energy, lamp.data.shape, lamp.data.size = power, 'DISK', size
    lamp.rotation_euler = (Vector((0, 0, .6))-lamp.location).to_track_quat('-Z', 'Y').to_euler()

samples = []
for frame in range(1, 62):
    scene.frame_set(frame)
    evaluated = falling.evaluated_get(bpy.context.evaluated_depsgraph_get())
    center = list(evaluated.matrix_world.translation)
    samples.append({'frame': frame, 'time_s': (frame-1)/60, 'center_m': center})
    if frame in (1, 13, 37):
        scene.render.filepath = str(OUT / f'box-fall-{frame:02d}.png')
        bpy.ops.render.render(write_still=True)

assert falling.animation_data is None, 'The box must have no prescribed animation.'
assert samples[12]['center_m'][2] < samples[0]['center_m'][2]-.15, 'Box must fall under gravity.'
assert abs(samples[-1]['center_m'][2]-(shelf_top+.125)) < .01, 'Box must settle on the shelf.'
assert all(s['center_m'][2] >= shelf_top+.125-.01 for s in samples), 'Box must not fall through the shelf.'
(OUT/'manifest.json').write_text(json.dumps({
    'generator': 'scripts/render_blender_physics.py',
    'blender_version': bpy.app.version_string,
    'simulation': 'Blender rigid-body physics (Bullet); no animation keyframes',
    'renderer': 'Cycles CPU; 32 samples; denoised',
    'mass_kg': 1, 'gravity_m_s2': list(scene.gravity),
    'shelf_top_m': shelf_top, 'box_size_m': [.25]*3,
    'samples': samples,
}, indent=2)+'\n')
print('Verified: gravity produces the fall; shelf contact stops the box; no position keyframes.')
