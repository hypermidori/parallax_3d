"""Head-only fitting study. Adapted from Chloe Wolfe's OGA-BY 3.0 FTChar2.
Reference measurements are kept in pixel space to avoid imaginary proportions.
"""
import bpy,bmesh,math,json,sys,argparse
from pathlib import Path
from mathutils import Vector
import numpy as np
P=argparse.ArgumentParser();P.add_argument('--name',default='head-fit-v01');A=P.parse_args(sys.argv[sys.argv.index('--')+1:])
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'/A.name;OUT.mkdir(exist_ok=False)
ref=bpy.data.images.load(str(ROOT/'references/player/turnaround-v01.png'))
source=bpy.data.objects['Cube']
original=source.data.copy()
for ob in list(bpy.data.objects):
    if ob!=source:bpy.data.objects.remove(ob,do_unlink=True)
source.parent=None;source.animation_data_clear();source.modifiers.clear()
source.location=(0,0,0);source.rotation_euler=(0,0,0);source.scale=(1,1,1)
source.hide_set(False);source.hide_render=False
bm=bmesh.new();bm.from_mesh(source.data)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<5.58],context='VERTS')
bm.to_mesh(source.data);bm.free()
# Keep the existing facial topology and remap measured height levels. The nose,
# lips, cheek and jaw remain connected surfaces, unlike the previous prototype.
zsrc=[5.58,5.665,5.90,6.08,6.34,6.59,6.84,7.03,7.278]
zdst=[-.018,0,.025,.047,.079,.12,.17,.203,.232]
for v in source.data.vertices:
    x,y,z=v.co
    zz=float(np.interp(z,zsrc,zdst))
    jaw=float(np.interp(z,[5.58,5.665,5.9,6.2,6.6,7.28],[.9,.80,.90,1,1,1]))
    v.co=(x*.135*jaw,y*.160-.018,zz)
source.name='Fitted_Base_Head'
source.data.materials.clear()

def mat(name,color,emission=False):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links
    bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=0
    if emission:
        bs.inputs['Emission Color'].default_value=(*color,1);bs.inputs['Emission Strength'].default_value=.3
    return m
skin=mat('Skin',(.91,.66,.49));hair=mat('Lavender hair',(.46,.32,.64))
hair2=mat('Lavender highlight',(.52,.38,.70));dark=mat('Graphite',(.025,.027,.046))
white=mat('Headset ivory',(.72,.77,.83));purple=mat('Headset violet',(.32,.08,.58),True)
source.data.materials.append(skin)
face=mat('Reference face projection',(.9,.64,.5));source.data.materials.append(face)
n=face.node_tree.nodes;l=face.node_tree.links
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'references/player/face-paint-v01.png'));t.interpolation='Linear'
uvn=n.new('ShaderNodeUVMap');uvn.uv_map='ReferenceProjection';l.new(uvn.outputs[0],t.inputs[0]);l.new(t.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
uv=source.data.uv_layers.new(name='ReferenceProjection')
for p in source.data.polygons:
    center=sum((source.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
    # Only the exposed front facial region receives the reference paint.
    p.material_index=int(center.y<-.045 and center.z<.142 and abs(center.x)<.089)
    p.use_smooth=True
    for li in p.loop_indices:
        c=source.data.vertices[source.data.loops[li].vertex_index].co
        uv.data[li].uv=(.5+c.x/.244,1-(570+(.071-c.z)*5900)/1254)
sub=source.modifiers.new('Editable facial surface','SUBSURF');sub.levels=2;sub.render_levels=2
parts=[source]

def mesh(name,vs,fs,m):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);parts.append(ob)
    return ob

def ribbon(name,centers,widths,depth=.005,material=hair,angle=0):
    # Catmull-Rom interpolation through individually traced silhouette controls.
    arr=[Vector(c) for c in centers];vs=[];rows=(len(arr)-1)*6+1;cols=12
    for ri in range(rows):
        f=ri/(rows-1)*(len(arr)-1);i=min(int(f),len(arr)-2);t=f-i
        p0=arr[max(i-1,0)];p1=arr[i];p2=arr[i+1];p3=arr[min(i+2,len(arr)-1)]
        c=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
        w=widths[i]*(1-t)+widths[i+1]*t
        for j in range(cols):
            theta=2*math.pi*j/cols;u=math.cos(theta)*w;v=math.sin(theta)*min(depth,w*.7)
            vs.append((c.x+u*math.cos(angle)-v*math.sin(angle),c.y+u*math.sin(angle)+v*math.cos(angle),c.z))
    fs=[(r*cols+j,r*cols+(j+1)%cols,(r+1)*cols+(j+1)%cols,(r+1)*cols+j) for r in range(rows-1) for j in range(cols)]
    ob=mesh(name,vs,fs,material)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def front_lock(name,points,widths,depths,material=hair):
    coords=[]
    for (x,py),y in zip(points,depths):
        xx=(x-355)*.002;zz=(210-py)*.002
        if zz>.14:
            # Keep roots outside the cap instead of intersecting its forehead rim.
            y=min(y,.012-.142*math.sqrt(max(0,1-(xx/.112)**2-((zz-.13)/.113)**2))-.003)
        coords.append((xx,y,zz))
    return ribbon(name,coords,[w*.002 for w in widths],.012 if 'framing' in name else .006,material,
                  (-.7 if 'Left' in name else .7) if 'framing' in name else 0)

# Hair cap derived from the actual head rather than an unrelated sphere.
cap=source.copy();cap.data=source.data.copy();cap.name='Scalp';bpy.context.scene.collection.objects.link(cap);parts.append(cap)
cap.data.materials.clear();cap.data.materials.append(hair)
bm=bmesh.new();bm.from_mesh(cap.data)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z < (.145 if v.co.y<0 else .065)],context='VERTS')
for v in bm.verts:
    v.co.x*=1.09;v.co.y=(v.co.y-.02)*1.075+.02;v.co.z=(v.co.z-.10)*1.055+.10
bm.to_mesh(cap.data);bm.free()
for p in cap.data.polygons:p.material_index=0

# Front locks: deliberately unequal silhouettes and tapered flat cross sections.
front_lock('Central sweeping fringe',[(351,104),(350,124),(352,145),(357,160),(366,174)],
           [7,14,14,9,.15],[-.064,-.108,-.126,-.127,-.119],hair2)
front_lock('Left swept fringe',[(344,104),(334,119),(330,139),(321,155),(314,167)],
           [6,10,10,6,.15],[-.063,-.096,-.12,-.121,-.112])
front_lock('Right swept fringe',[(368,105),(378,123),(382,140),(389,154),(395,164)],
           [6,11,10,6,.15],[-.061,-.094,-.119,-.116,-.10],hair2)
front_lock('Left cheek framing',[(318,117),(308,145),(306,181),(310,213),(320,241),(328,258)],
           [7,11,12,10,6,.2],[-.035,-.069,-.069,-.060,-.052,-.043])
front_lock('Right cheek framing',[(397,117),(403,147),(402,181),(395,215),(383,241),(377,257)],
           [7,11,11,10,6,.2],[-.035,-.069,-.068,-.060,-.05,-.04],hair2)
front_lock('Left small temple curl',[(324,135),(318,166),(318,185),(328,199)],
           [6,8,6,.1],[-.083,-.108,-.105,-.094],hair2)
front_lock('Right small temple curl',[(388,135),(396,165),(394,185),(382,200)],
           [6,8,6,.1],[-.082,-.108,-.105,-.094])

# Back hair is shaped from the profile and back-view silhouette, with larger
# overlapping sheet-like locks. The sweep is toward viewer-left from the rear.
for i in range(6):
    x=(i-2.5)*.027
    endx=x+.07+.013*i
    endz=-.275+.018*abs(i-2)
    ribbon(f'Back hair panel {i}',[(x*.48,.049,.230),(x*.94,.112,.174),
       (x*1.07,.130,.077),(x+.018,.151,-.018),(x+.05,.181,-.11),
       (endx,.184,endz+.045),(endx-.025,.14,endz)],
       [.013,.023,.030,.037,.042,.024,.0003],.005,hair if i%2 else hair2)
# Soft side silhouettes connect the crown to the flowing back mass.
for s in (-1,1):
    ribbon('Outer hair silhouette',[(s*.066,.00,.207),(s*.1,.054,.139),
        (s*.105,.089,.03),(s*.117,.11,-.073),(s*.165,.14,-.16),(s*.195,.145,-.171)],
        [.018,.050,.074,.073,.050,.0002],.019,hair,angle=s*math.pi/2)

def cylinder(name,loc,r,depth,m,rotation=(0,math.pi/2,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=depth,location=loc,rotation=rotation)
    ob=bpy.context.object;ob.name=name;ob.data.materials.append(m);parts.append(ob)
    be=ob.modifiers.new('Machined edge','BEVEL');be.width=.0015;be.segments=2
    for p in ob.data.polygons:p.use_smooth=True
    return ob
for s in (-1,1):
    cylinder('Headset housing',(s*.111,.004,.128),.038,.025,dark)
    cylinder('Headset violet',(s*.126,.004,.128),.029,.003,purple)
    cylinder('Headset center',(s*.129,.004,.128),.022,.003,dark)
    # A genuinely tapered fin following the reference, with an inset dark face.
    vs=[(s*.103,-.003,.161),(s*.12,.007,.255),(s*.135,.006,.23),(s*.141,-.004,.17)]
    vs+= [(x,y+.009,z) for x,y,z in vs]
    ob=mesh('Communication fin',vs,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],white)
    mesh('Fin inset',[(s*.118,-.006,.183),(s*.121,.003,.235),(s*.13,.002,.218),(s*.132,-.006,.181)],[(0,1,2,3)],dark)

# Small neck stub for judging the chin-neck transition, no full-body modeling.
cylinder('Neck study',(0,.007,-.020),.031,.075,skin,rotation=(0,0,0))

# Recalculate normals on created surfaces, preserve the editable source mesh.
for ob in parts:
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()

s=bpy.context.scene;s.frame_set(1);s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
s.world=bpy.data.worlds.new('Neutral world');s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.55,.55,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.6
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0
s.render.resolution_x=720;s.render.resolution_y=900;s.render.resolution_percentage=100
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power in [('Key',(-1,-2,2),85),('Fill',(1,-1,1),35)]:
    bpy.ops.object.light_add(type='AREA',location=loc);li=bpy.context.object;li.name=name;li.data.energy=power;li.data.size=2;aim(li,(0,0,.05))
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Study camera';cam.data.type='ORTHO';cam.data.ortho_scale=.62;s.camera=cam
target=Vector((0,0,-.015))
for name,loc in [('front',(0,-3,-.015)),('side',(3,0,-.015)),('back',(0,3,-.015)),('three-quarter',(.95,-2,.15))]:
    cam.location=loc;aim(cam,target);s.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
# Geometry-only inspection: disable face projection and remove colored materials.
clay=mat('Unpainted clay',(.48,.48,.48));s.view_layers[0].material_override=clay
cam.location=(.95,-2,.15);aim(cam,target);s.render.filepath=str(OUT/'clay-three-quarter.png');bpy.ops.render.render(write_still=True)
s.view_layers[0].material_override=None

# Registered reference planes are part of the .blend, hidden only for renders.
refs=bpy.data.collections.new('REFERENCE / orthographic matching');s.collection.children.link(refs)
for name,loc,rot in [('Front',(0,.31,0),(math.pi/2,0,0)),('Side',(-.31,0,0),(math.pi/2,0,math.pi/2))]:
    ob=bpy.data.objects.new('Reference '+name,None);ob.empty_display_type='IMAGE';ob.data=ref
    ob.empty_display_size=1774*.002;ob.color[3]=.25;ob.empty_image_depth='BACK';ob.location=loc;ob.rotation_euler=rot
    # Full sheet is offset so its selected view's chin is the modeling origin.
    ob.empty_image_offset=(-355/1774,-(887-210)/887) if name=='Front' else (-890/1774,-(887-210)/887)
    refs.objects.link(ob);ob.hide_render=True;ob.hide_set(True)
for ob in s.objects:ob.select_set(False)
source.select_set(True);bpy.context.view_layer.objects.active=source
for im in (ref,t.image):im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'head-study.blend'))
data={'source':'Chloe Wolfe / 3D Female Anime Base - rigged and textured',
      'source_url':'https://opengameart.org/content/3d-female-anime-base-rigged-and-textured',
      'license':'OGA-BY 3.0','base_head_vertices':len(source.data.vertices),
      'method':'Existing facial topology deformed with measured height/profile mapping; individually traced hair sheets.',
      'scope':'Head and hair only. Not a finished game asset.',
      'landmarks':{'reference_chin_px':[355,210],'reference_crown_y':98,'pixel_scale_m':.002}}
(OUT/'study.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print('STUDY COMPLETE',OUT)
