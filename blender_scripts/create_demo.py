"""Build a small map and an unrigged robot as an end-to-end pipeline example."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asset_utils import aim, cube, export_collection, material, mesh_stats

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
parser.add_argument('--skip-render', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
out = Path(args.output).resolve()
out.mkdir(parents=True, exist_ok=False)
random.seed(42)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.12, 0.18, 0.26, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.5

map_col = bpy.data.collections.new('Map')
robot_col = bpy.data.collections.new('Character')
scene.collection.children.link(map_col)
scene.collection.children.link(robot_col)
grass = material('Grass', (0.18, 0.40, 0.29))
earth = material('Earth', (0.13, 0.20, 0.23))
stone = material('Stone', (0.40, 0.50, 0.53))
path_mat = material('Path', (0.68, 0.62, 0.45))
bark = material('Bark', (0.26, 0.15, 0.08))
leaves = material('Leaves', (0.12, 0.33, 0.22))
orange = material('Robot orange', (0.95, 0.30, 0.06), 0.45)
dark = material('Robot joints', (0.035, 0.07, 0.10), 0.4, 0.3)
visor = material('Robot visor', (0.15, 0.80, 0.92), 0.25, 0.2)
cube('Island foundation', (0, 0, -0.45), (12, 10, 0.8), earth, map_col, 0.16)
cube('Ground', (0, 0, -0.08), (11.9, 9.9, 0.16), grass, map_col, 0.07)
for y in range(-4, 5):
    cube(f'Path {y}', (0.5, y, 0.035), (1.9, 0.86, 0.07), path_mat, map_col, 0.04)
for x in (-3.8, 3.8):
    cube('Gate pillar', (x, 2.5, 1.25), (0.75, 0.85, 2.5), stone, map_col, 0.06)
cube('Gate lintel', (0, 2.5, 2.7), (8.5, 0.9, 0.5), stone, map_col, 0.08)
for i, (x, y) in enumerate([(-4,-2), (-3.5,0.7), (4,-2.3), (4,3.9), (-4.7,3.7)]):
    cube(f'Tree trunk {i}', (x,y,0.65), (0.3,0.3,1.3), bark, map_col, 0.02)
    for tier in range(2):
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=0.85-tier*0.22, radius2=0,
                                        depth=1.5, location=(x,y,1.65+tier*0.65))
        obj = bpy.context.object
        obj.name = f'Tree canopy {i}-{tier}'
        obj.data.materials.append(leaves)
        for old in list(obj.users_collection):
            old.objects.unlink(obj)
        map_col.objects.link(obj)
for i in range(7):
    x, y = random.choice((-1, 1))*random.uniform(2, 5), random.uniform(-4, 1)
    cube(f'Rock {i}', (x,y,0.2), (0.6,0.5,0.4), stone, map_col, 0.12)

# Character is authored at its own origin; feet touch Z=0. Height is ~1.9 m.
for side in (-1, 1):
    cube(f'Foot {side}', (side*0.23,-0.08,0.13), (0.33,0.48,0.26), dark, robot_col, 0.04)
    cube(f'Leg {side}', (side*0.23,0,0.48), (0.24,0.27,0.5), orange, robot_col, 0.04)
    cube(f'Arm {side}', (side*0.57,0,1.08), (0.22,0.3,0.64), orange, robot_col, 0.05)
cube('Body', (0,0,1.04), (0.78,0.43,0.68), orange, robot_col, 0.08)
cube('Chest panel', (0,-0.23,1.06), (0.32,0.04,0.23), dark, robot_col, 0.015)
cube('Neck', (0,0,1.45), (0.21,0.23,0.17), dark, robot_col, 0.02)
cube('Head', (0,0,1.68), (0.65,0.48,0.43), orange, robot_col, 0.07)
cube('Visor', (0,-0.25,1.70), (0.46,0.055,0.19), visor, robot_col, 0.03)

export_collection(map_col, out / 'map.glb')
export_collection(robot_col, out / 'character.glb')
stats = {'map': mesh_stats(map_col.all_objects), 'character': mesh_stats(robot_col.all_objects)}
# Position the character for the combined preview, after exporting it at the origin.
for obj in robot_col.objects:
    obj.location.x += 0.5
    obj.location.y -= 1.3
bpy.ops.object.camera_add(location=(14,-19,16))
camera = bpy.context.object
camera.name = 'Preview camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 17
aim(camera, (0,0,0.5))
scene.camera = camera
bpy.ops.object.light_add(type='AREA', location=(1,-4,11))
key = bpy.context.object
key.name = 'Key light'
key.data.energy = 1800
key.data.shape = 'DISK'
key.data.size = 8
aim(key, (0,0,0))
bpy.ops.object.light_add(type='SUN', location=(-5,3,8))
bpy.context.object.data.energy = 1.5
bpy.context.object.rotation_euler = (math.radians(25), math.radians(-20), math.radians(-30))
scene.render.filepath = str(out / 'preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'scene.blend'))
if not args.skip_render:
    bpy.ops.render.render(write_still=True)
manifest = {
    'blender_version': bpy.app.version_string, 'seed': 42,
    'units': 'meters', 'blender_up_axis': 'Z', 'glb_up_axis': 'Y',
    'character': 'Unrigged static robot; no animation or collision meshes.',
    'stats': stats, 'rendered': not args.skip_render,
    'files': ['scene.blend', 'map.glb', 'character.glb'] + ([] if args.skip_render else ['preview.png']),
}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('BUILD COMPLETE:', out)
