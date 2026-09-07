"""Inspect exported GLB structure and reimport the actual rigged asset."""
import argparse
import json
import struct
import sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser();p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.output).resolve()
data=(out/'player.glb').read_bytes()
magic,version,length=struct.unpack_from('<III',data)
assert magic==0x46546c67 and version==2 and length==len(data)
chunk_len,chunk_type=struct.unpack_from('<II',data,12)
assert chunk_type==0x4e4f534a
doc=json.loads(data[20:20+chunk_len])
assert len(doc['skins'])==1
assert len(doc['animations'])>=1
assert len(doc['materials'])==1
assert len(doc['images'])==2 and all('bufferView' in im for im in doc['images'])
primitives=[p for m in doc['meshes'] for p in m['primitives']]
assert all('JOINTS_0' in p['attributes'] and 'WEIGHTS_0' in p['attributes'] and 'TEXCOORD_0' in p['attributes'] for p in primitives)
manifest=json.loads((out/'manifest.json').read_text())
triangles=sum(doc['accessors'][p['indices']]['count']//3 for p in primitives)
assert triangles==manifest['triangles'] and 3000<=triangles<=6000
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(out/'player.glb'),disable_bone_shape=True)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
assert len(meshes)==1 and len(rigs)==1
ob=meshes[0];rig=rigs[0]
assert len(rig.data.bones)==manifest['bones']
assert all(v.groups and abs(sum(g.weight for g in v.groups)-1)<.001 for v in ob.data.vertices)
assert bpy.data.actions
scene=bpy.context.scene
scene.frame_set(1)
def points():
    dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg)
    me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return pts
p1=points();scene.frame_set(13);p2=points()
motion=max((x-y).length for x,y in zip(p1,p2))
assert motion>.005, f'Animation does not move mesh: {motion}'
result={'status':'passed','triangles':triangles,'mesh_objects':len(meshes),
        'material_primitives':len(primitives),'bones':len(rig.data.bones),
        'embedded_textures':len(doc['images']),'animations':[a['name'] for a in doc['animations']],
        'animation_displacement_m':round(motion,5),'all_vertices_weighted':True}
(out/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('GLB VERIFIED',json.dumps(result))
