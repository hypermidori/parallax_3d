import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'output/head-study'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
im=bpy.data.images.load(str(root/'references/player/turnaround-v01.png'))
print('REFERENCE_SIZE',im.size[:])
mat=bpy.data.materials.new('Reference');mat.use_nodes=True
n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
t=n.new('ShaderNodeTexImage');t.image=im;e=n.new('ShaderNodeEmission');o=n.new('ShaderNodeOutputMaterial')
l.new(t.outputs[0],e.inputs[0]);l.new(e.outputs[0],o.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=2);ob=bpy.context.object;ob.data.materials.append(mat)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.view_settings.view_transform='Standard';s.view_settings.look='None'
bpy.ops.object.camera_add(location=(0,0,3));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2;s.camera=cam
s.render.resolution_x=600;s.render.resolution_y=750;s.render.resolution_percentage=100
for name,region in [('front',(265,80,470,337)),('side',(783,80,988,337)),('back',(1319,80,1524,337))]:
    x0,y0,x1,y1=region
    ob.scale=(.8,1,1)
    for loop in ob.data.uv_layers.active.data:
        u,v=loop.uv[:]
        # Reset UV for each view using original plane corner coordinates.
    for p in ob.data.polygons:
        for li in p.loop_indices:
            co=ob.data.vertices[ob.data.loops[li].vertex_index].co
            u=(co.x+1)/2;v=(co.y+1)/2
            ob.data.uv_layers.active.data[li].uv=((x0+u*(x1-x0))/im.size[0],1-(y1-v*(y1-y0))/im.size[1])
    s.render.filepath=str(out/f'reference-{name}.png');bpy.ops.render.render(write_still=True)
