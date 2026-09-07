"""Shared image-textured mesh tools for the support enemy models."""
import bpy,math,json,bmesh
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
TILES={'orange':(.01,.51,.323,.99),'olive':(.344,.51,.657,.99),'ivory':(.677,.51,.99,.99),
 'metal':(.01,.01,.323,.49),'black':(.344,.01,.657,.49),
 'amber':(.687,.397,.98,.475),'red':(.687,.277,.98,.355),
 'steel':(.687,.15,.98,.23),'hazard':(.687,.025,.98,.10)}
M={};parts=[];anchors=[];image=None
def begin(prefix):
    global M,parts,anchors,image
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    M={};parts=[];anchors=[]
    image=bpy.data.images.load(str(ROOT/'public/assets/support-enemies-atlas.png'));image.pack()
    for name in TILES:
        mat=bpy.data.materials.new(prefix+' '+name);mat.use_nodes=True
        shader=mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Roughness'].default_value=.62
        shader.inputs['Metallic'].default_value=.2 if name in ['orange','olive','ivory'] else .55
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
        mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
        if name in ['amber','red']:
            mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Emission Color'])
            shader.inputs['Emission Strength'].default_value=.85
            shader.inputs['Metallic'].default_value=.15
        M[name]=mat
def anchor(name,position):
    ob=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ob);ob.location=position;anchors.append(ob);return ob
def mesh(name,vertices,faces,materials,face_materials=None,bevel=0):
    me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    for mat in materials:me.materials.append(M[mat])
    # Project each face on its dominant plane, using object-local dimensions.
    uv=me.uv_layers.new(name='Painted atlas UV')
    bounds=[(min(v[i] for v in vertices),max(v[i] for v in vertices)) for i in range(3)]
    for face in me.polygons:
        mi=face_materials[face.index] if face_materials else 0;face.material_index=mi
        tile=TILES[materials[mi]]
        dominant=max(range(3),key=lambda i:abs(face.normal[i]))
        axes=[i for i in range(3) if i!=dominant]
        for li,vi in zip(face.loop_indices,face.vertices):
            coords=[]
            for axis in axes:
                lo,hi=bounds[axis];coords.append((vertices[vi][axis]-lo)/max(hi-lo,.001))
            uv.data[li].uv=(tile[0]+coords[0]*(tile[2]-tile[0]),tile[1]+coords[1]*(tile[3]-tile[1]))
    # Recalculate normals for mirrored polygon outlines too.
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    if bevel:
        mod=ob.modifiers.new('Armor edge bevel','BEVEL');mod.width=bevel;mod.segments=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    parts.append(ob);ob.select_set(False);return ob
def slab(name,outline,z0,z1,mat='blue',edge='ivory',bevel=.015):
    n=len(outline);v=[(x,y,z) for z in [z0,z1] for x,y in outline]
    return mesh(name,v,[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],
                [mat,edge],[1,0]+[1]*n,bevel)
def loft(name,stations,cx=0,colors=('ivory','blue','metal'),cap_end=True):
    v=[]
    for y,w,b,t in stations:
        d=(t-b)*.24
        v.extend([(cx+x,y,z) for x,z in [(-w*.62,t),(w*.62,t),(w,t-d),(w,b+d),(w*.62,b),(-w*.62,b),(-w,b+d),(-w,t-d)]])
    f=[tuple(reversed(range(8)))];fm=[2]
    for j in range(len(stations)-1):
        for i in range(8):
            f.append((j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i))
            fm.append(0 if i==0 else 1 if i in [1,7] else 2)
    if cap_end:f.append(tuple(range(len(v)-8,len(v))));fm.append(2)
    return mesh(name,v,f,list(colors),fm,.018)
def ring(name,cx,y,cz,w,h,depth,mat='ivory',inset=.13):
    # Clipped rectangular intake with a recessed interior, not a solid box face.
    outline=[(-.63*w,-h),(.63*w,-h),(w,-.63*h),(w,.63*h),(.63*w,h),(-.63*w,h),(-w,.63*h),(-w,-.63*h)]
    inner=[(x*(w-inset)/w,z*(h-inset)/h) for x,z in outline]
    vertices=[(cx+x,yy,cz+z) for yy,loop in [(y,outline),(y,inner),(y-depth,inner),(y-depth,outline)] for x,z in loop]
    f=[];fm=[]
    for i in range(8):
        j=(i+1)%8
        f.extend([(i,j,j+8,i+8),(i+8,j+8,j+16,i+16),(i,j,j+24,i+24)])
        fm.extend([0,1,0])
    return mesh(name,vertices,f,[mat,'black'],fm,.012)
def cylinder(name,center,radius,length,mat='metal',axis='Y',count=12,r2=None):
    r2=radius if r2 is None else r2
    v=[]
    for dist,r in [(-length/2,radius),(length/2,r2)]:
        for i in range(count):
            a=2*math.pi*i/count
            p=(r*math.cos(a),dist,r*math.sin(a)) if axis=='Y' else (r*math.cos(a),r*math.sin(a),dist)
            v.append(tuple(Vector(center)+Vector(p)))
    f=[tuple(reversed(range(count))),tuple(range(count,2*count))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    return mesh(name,v,f,[mat])
def beam(name,a,b,radius,mat='metal',count=8):
    ob=cylinder(name,(0,0,0),radius,(Vector(b)-Vector(a)).length,mat,'Z',count)
    ob.location=(Vector(a)+Vector(b))/2;ob.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return ob
def panel(name,x,y,z,w,h,mat='blue'):
    return slab(name,[(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)],z,z+.028,mat,mat,.009)

def finish(slug,title,target=(0,0,0),span=7):
    out=ROOT/'output'/slug;out.mkdir(parents=True,exist_ok=True)
    root=bpy.data.objects.new(title,None);bpy.context.collection.objects.link(root)
    for ob in parts:
        bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        ob.select_set(False);ob.parent=root
    for ob in anchors:ob.parent=root
    root['design']=title;root['forward_axis']='+Y in Blender / -Z in glTF'
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.14,.19,.26,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    for loc,power,size,color in [((-4,4,7),950,6,(1,.9,.78)),((5,-3,6),1300,5,(.5,.73,1)),((0,7,4),600,4,(.8,.9,1))]:
        bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.size=size;light.data.color=color
        light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=Vector(target)+Vector((8,10,7)));cam=bpy.context.object
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=span;scene.camera=cam
    scene.render.resolution_x=1000;scene.render.resolution_y=850;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.3
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(slug+'.blend')))
    bpy.ops.object.select_all(action='DESELECT')
    for ob in parts:ob.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();model=parts[0];model.name=title+' painted hull'
    root.select_set(True)
    for ob in anchors:ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets'/(slug+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False,export_extras=True)
    model.data.calc_loop_triangles()
    stats={'triangles':len(model.data.loop_triangles),'vertices':len(model.data.vertices),'uv':bool(model.data.uv_layers),'materials':len(model.data.materials),
     'dimensions':list(model.dimensions),'shot_origin':list(anchors[0].location) if anchors else None}
    (out/'manifest.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    for view,location,rotation in [('beauty',None,None),('top',(0,0,15),(0,0,math.pi)),('front',(0,14,target[2]),(math.pi/2,0,math.pi))]:
        if location:cam.location=location
        if rotation:cam.rotation_euler=rotation
        scene.render.filepath=str(out/(view+'.png'));bpy.ops.render.render(write_still=True)
    print('MODEL_COMPLETE',slug,json.dumps(stats),flush=True)
