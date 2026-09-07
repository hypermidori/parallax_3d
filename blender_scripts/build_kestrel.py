"""Azure Kestrel: model against references/enemies/kestrel/design-v01.png.
Blender CLI: --background --factory-startup --python-exit-code 1 --python thisfile
Every surface uses an embedded authored image atlas. Units: meters, +Y nose.
"""
import bpy, math, json, bmesh
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/kestrel';OUT.mkdir(parents=True,exist_ok=True)
AS=ROOT/'public/assets'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
image=bpy.data.images.load(str(AS/'kestrel-atlas.png'));image.pack()
TILES={'blue':(.02,.52,.48,.98),'ivory':(.52,.52,.98,.98),
       'metal':(.02,.02,.48,.48),'black':(.54,.395,.96,.48),
       'cyan':(.54,.27,.96,.355),'orange':(.54,.16,.96,.245),'steel':(.54,.02,.96,.105)}
M={}
for name in TILES:
    m=bpy.data.materials.new('Kestrel '+name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Roughness'].default_value=.6 if name in ['blue','ivory'] else .45
    p.inputs['Metallic'].default_value=.18 if name in ['blue','ivory'] else .65
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    if name=='cyan':
        m.node_tree.links.new(tex.outputs['Color'],p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value=1.0
        p.inputs['Metallic'].default_value=.2
    M[name]=m
parts=[]
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
# Plan view is traced from the left orthographic view, retaining its long nose.
loft('Central chisel fuselage',[(-4.3,.27,-.12,.35),(-3.7,.48,-.24,.62),(-2.65,.62,-.35,.9),
    (-1.35,.67,-.4,.85),(-.1,.64,-.42,.65),(1.15,.57,-.38,.43),(2.7,.4,-.22,.24),(3.85,.25,-.075,.15),(4.42,.22,-.02,.09)])
# Long thin recessed spine, with raised armor over either side.
for j,(y,z,w) in enumerate([(-3.15,.78,.26),(-2.6,.92,.27),(-2,.905,.26),(-1.4,.875,.25),(-.85,.8,.25)]):
    panel('Dorsal blue plate '+str(j),0,y,z,w*2,.5,'blue')
    if j in [0,2,4]:panel('Dorsal cyan strip '+str(j),0,y,z+.04,.22,.095,'cyan')
for j in range(6):
    y=1.65+j*.3;z=.4-j*.043
    panel('Nose graphite inset '+str(j),0,y,z,.22,.25,'black')
    if j<4:panel('Nose status segment '+str(j),0,y,z+.035,.13,.08,'cyan')
# Faceted saddle seats the sensor into the fuselage instead of a floating disk.
loft('Sensor armored saddle',[(-.85,.47,.35,.85),(-.1,.56,.27,.82),(.55,.50,.17,.63),(1.48,.30,.10,.28)],colors=('blue','ivory','metal'))
for j,(y,z) in enumerate([(-1.1,.86),(-.67,.86),(-.24,.84)]):
    panel('Central recessed radiator '+str(j),0,y,z,.25,.32,'black')
    for k in [-.08,.02,.12]:panel('Radiator louver',0,y+k,z+.032,.21,.025,'metal')
# Faceted sensor bezel leaning forward: visible both from above and in flight.
for radius,depth,mat,offset in [(.53,.22,'metal',0),(.43,.235,'steel',.02),(.355,.25,'black',.045),(.265,.26,'cyan',.07)]:
    ob=cylinder('Hexagonal optical sensor '+mat,(0,0,0),radius,depth,mat,'Z',6)
    ob.rotation_euler.x=-math.pi/4;ob.location=(0,.88+offset,.67+offset)
for sign in [-1,1]:
    label='Port' if sign<0 else 'Starboard'
    # Broad swept wing with physically thick edge rail and inset blue paint.
    outline=[(sign*x,y) for x,y in [(1.7,-1.9),(3.97,-.16),(4,.30),(1.9,.65),(1.5,.36)]]
    slab(label+' wing structural shell',outline,-.13,.10,'ivory','metal',.035)
    inner=[(sign*x,y) for x,y in [(1.89,-1.56),(3.73,-.12),(3.75,.15),(1.97,.45),(1.75,.25)]]
    slab(label+' swept blue wing armor',inner,.115,.17,'blue','blue',.012)
    # Orange insignia and ivory outer tip. No texture-free decals.
    slab(label+' wing warning arrow',[(sign*3.12,-.4),(sign*3.3,-.28),(sign*3.1,-.23)],.183,.19,'orange','orange',0)
    # Separate wing-panel seams rather than triangulation masquerading as detail.
    for x,y in [(2.36,-.85),(2.98,-.4)]:
        beam(label+' wing panel seam',(sign*x,y,.19),(sign*(x+.05),.34,.19),.011,'black',4)
    # Engine trunks are tapered octagonal sections, with external blue armor.
    cx=sign*1.12
    loft(label+' engine trunk',[(-3.48,.36,-.23,.42),(-3.04,.49,-.37,.76),(-1.65,.5,-.4,.94),(-.15,.49,-.4,.9),(1.36,.48,-.32,.8)],cx,('blue','ivory','metal'),cap_end=False)
    for j,y in enumerate([-2.7,-1.55,-.38,.78]):
        panel(label+' engine service panel '+str(j),cx,y,.82 if j==0 else .96 if j<3 else .88,.48,.52,'blue' if j%2 else 'ivory')
        panel(label+' service latch '+str(j),cx,y+.15,1.005 if 0<j<3 else .93,.07,.12,'steel')
    # Tapered blue fairing projects beside the slender central nose.
    slab(label+' forward engine fairing',[(sign*.68,.9),(sign*1.58,.6),(sign*1.56,1.52),(sign*.28,3.65),(sign*.2,3.1)],-.17,.14,'blue','ivory',.025)
    ring(label+' intake armored lip',cx,1.58,.35,.49,.58,.32,'ivory',.105)
    ring(label+' intake steel inner lip',cx,1.59,.35,.38,.45,.17,'steel',.04)
    ring(label+' intake cyan gasket',cx,1.39,.35,.325,.395,.02,'cyan',.017)
    # Recessed dark wall + 5 real louvers give the frontal opening depth.
    ring(label+' intake pocket',cx,1.21,.35,.32,.39,.045,'black',.31)
    for j in range(5):
        z=.075+j*.135
        beam(label+' intake blade '+str(j),(cx-.24,1.30,z),(cx+.24,1.30,z+.018),.032,'metal',4)
    panel(label+' nacelle orange warning',cx,1.59,.96,.16,.075,'orange')
    # Rear exhaust is a true layered nozzle, distinct from the rectangular intake.
    cylinder(label+' exhaust collar',(cx,-3.42,.24),.4,.42,'metal',count=12)
    cylinder(label+' exhaust lip',(cx,-3.67,.24),.33,.16,'steel',count=12)
    cylinder(label+' exhaust black cavity',(cx,-3.765,.24),.265,.02,'black',count=12)
    cylinder(label+' exhaust glow',(cx,-3.78,.24),.18,.023,'cyan',count=12)
    for j in range(8):
        a=j*math.pi/4
        beam(label+' nozzle rib '+str(j),(cx+math.cos(a)*.35,-3.25,.24+math.sin(a)*.35),(cx+math.cos(a)*.32,-3.65,.24+math.sin(a)*.32),.025,'metal',4)
    # Canted tail fin: inclined solid plate with a swept outline and ivory cap.
    yz=[(-3.3,.68),(-4.08,2.36),(-3.88,2.49),(-2.0,.83)]
    verts=[]
    for thickness in [-.055,.055]:
        for y,z in yz:verts.append((sign*(1.15+(z-.68)*.45+.25*(y+3.3))+thickness,y,z))
    mesh(label+' swept tail fin',verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],['blue','ivory','metal'],[0,0,2,1,1,2],.018)
    # A gun pod with collars, reduced muzzle and a recessed bore under each wing.
    gx=sign*3.22
    beam(label+' gun mount',(gx,.01,-.08),(gx,.01,-.34),.14,'metal',8)
    for j,(y,r,l,mat) in enumerate([(.02,.19,.45,'metal'),(.36,.115,.36,'steel'),(.62,.14,.16,'metal'),(.72,.09,.035,'black')]):
        cylinder(label+' gun barrel '+str(j),(gx,y,-.39),r,l,mat,count=12)
    panel(label+' wing tip lamp',sign*3.78,.0,.175,.07,.1,'cyan')
# Apply all geometry transforms, retain artist-readable parts in the .blend.
for ob in parts:
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    ob.select_set(False)
# Consolidate by material for few draw calls; export has real UVs on every face.
# Keep the .blend editable before batching the export.
root=bpy.data.objects.new('Azure Kestrel',None);bpy.context.collection.objects.link(root)
for ob in parts:ob.parent=root
root['source_design']='references/enemies/kestrel/design-v01.png'
root['forward_axis']='+Y in Blender / -Z in glTF'
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.17,.22,.3,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
for loc,power,size,color in [((-5,3,9),1800,7,(1,.9,.78)),((5,-4,7),2200,6,(.5,.73,1)),((0,8,5),1000,5,(.75,.9,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.data.color=color
    light.rotation_euler=(Vector((0,0,.3))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(10,12,10));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=12.3;scene.camera=cam
scene.render.resolution_x=1100;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.45
scene.render.image_settings.file_format='PNG'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'azure-kestrel.blend'))
# Merge into one editable mesh, keeping the seven atlas material slots.
bpy.ops.object.select_all(action='DESELECT')
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();model=parts[0];model.name='Kestrel painted hull'
bpy.ops.export_scene.gltf(filepath=str(AS/'azure-kestrel.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=False)
model.data.calc_loop_triangles()
stats={'triangles':len(model.data.loop_triangles),'vertices':len(model.data.vertices),'texture':image.name,'uv':bool(model.data.uv_layers),'dimensions':list(model.dimensions),'materials':len(model.data.materials)}
(OUT/'manifest.json').write_text(json.dumps(stats,indent=2))
scene.render.filepath=str(OUT/'beauty.png');bpy.ops.render.render(write_still=True)
cam.location=(0,0,18);cam.rotation_euler=(0,0,math.pi);cam.data.ortho_scale=11.5
scene.render.filepath=str(OUT/'top.png');bpy.ops.render.render(write_still=True)
print('KESTREL_COMPLETE',json.dumps(stats),flush=True)

