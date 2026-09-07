import bpy, json
from mathutils import Vector
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'output/head-study';out.mkdir(exist_ok=True)
ob=bpy.data.objects['Cube']
print('TRANSFORM',ob.location[:],ob.rotation_euler[:],ob.scale[:])
print('MODS',[(m.name,m.type) for m in ob.modifiers])
print('RANGE',[(min(v.co[i] for v in ob.data.vertices),max(v.co[i] for v in ob.data.vertices)) for i in range(3)])
print('GROUPS',[(v.index,v.name) for v in ob.vertex_groups if 'head' in v.name.lower()])
for x in list(bpy.data.objects):
    if x!=ob:bpy.data.objects.remove(x,do_unlink=True)
ob.parent=None;ob.animation_data_clear()
for m in list(ob.modifiers):
    if m.type=='ARMATURE':ob.modifiers.remove(m)
ob.hide_set(False);ob.hide_render=False
mat=bpy.data.materials.new('Clay');mat.diffuse_color=(.65,.65,.65,1);mat.use_nodes=True
ob.data.materials.clear();ob.data.materials.append(mat)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16
s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[1].default_value=.6
s.view_settings.view_transform='Standard'
for loc,en in [((2,-3,4),240),((-2,-1,3),140)]:
    bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=en;l.data.size=3
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.62
s.render.resolution_x=700;s.render.resolution_y=700;s.render.resolution_percentage=100
for name,loc in [('front',(0,-4,1.82)),('side',(4,0,1.82))]:
    cam.location=loc;cam.rotation_euler=(Vector((0,0,1.82))-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(out/f'base-{name}.png');bpy.ops.render.render(write_still=True)
print('HEADVERTS',[(v.index,tuple(round(c,4) for c in v.co)) for v in ob.data.vertices if v.co.z>1.65][:12])
