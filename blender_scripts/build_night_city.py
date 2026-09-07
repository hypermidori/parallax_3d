"""Textured, actual 3D city kit and rail stage. Blender 4.5 background build.
The generated architectural atlas is UV mapped onto every environment mesh.
Geometry is batched per material and 180 m district chunk for game culling.
"""
import bpy,math,json,random,bmesh
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];AS=ROOT/'public/assets';OUT=ROOT/'output/night-city';OUT.mkdir(parents=True,exist_ok=True)
ROUTE=json.loads((ROOT/'config/city-route.json').read_text())
LOOP_START=ROUTE['loopStart'];CHUNK_LENGTH=ROUTE['chunkLength'];STORY_CHUNKS=LOOP_START//CHUNK_LENGTH
random.seed(42)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
atlas=bpy.data.images.load(str(AS/'city-atlas.png'));roadim=bpy.data.images.load(str(AS/'road-original.png'))
atlas.pack();roadim.pack()
M={}
def material(name,image=atlas,color=(1,1,1),emission=0,rough=.65,metal=.2):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links
    p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    tex=n.new('ShaderNodeTexImage');tex.image=image;l.new(tex.outputs['Color'],p.inputs['Base Color'])
    if emission:
        l.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=emission
    m.diffuse_color=(*color,1);M[name]=m;return m
material('Office windows',emission=1.6,rough=.37,metal=.45)
material('Concrete facade',emission=.38,rough=.72)
material('Architectural metal',rough=.48,metal=.65)
material('Concrete paving',rough=.82,metal=.05)
material('Road asphalt',image=roadim,rough=.55,metal=.18)
# A tiny authored RGB texture is generated in Blender for UV-mapped light strips,
# lane paint and vehicle armor. No environment surface falls back to an untextured material.
palette=bpy.data.images.new('surface-palette',width=16,height=16,alpha=True)
colors=[(.025,.62,1),(.85,.13,.65),(.88,.72,.42),(.68,.78,.82),(.1,.24,.13),(.28,.36,.39),(.005,.016,.034),(.9,.25,.06)]
pix=[]
for y in range(16):
    for x in range(16):
        c=colors[(x//4)+(y//8)*4];noise=1-((x*7+y*3)%5)*.025;pix.extend([*(v*noise for v in c),1])
palette.pixels=pix;palette.filepath_raw=str(AS/'surface-palette.png');palette.file_format='PNG';palette.save();palette.pack()
material('Illuminated details',image=palette,emission=4,rough=.4,metal=.1)
material('Painted details',image=palette,rough=.5,metal=.35)
TILES={'glass':(.004,.504,.496,.996),'concrete':(.504,.504,.996,.996),'metal':(.004,.004,.496,.496),'paving':(.504,.004,.996,.496),'road':(0,0,1,1)}
for i in range(8):
    x=i%4;y=i//4;TILES['p'+str(i)]=((x*4+.6)/16,(y*8+.6)/16,(x*4+3.4)/16,(y*8+7.4)/16)
BUCKET={};chunk='city_00';rootname=None
def quad(vs,mat,tile='metal',uv=None):
    key=(chunk,mat);b=BUCKET.setdefault(key,{'v':[],'f':[],'uv':[]});k=len(b['v']);b['v'].extend(vs);b['f'].append(tuple(range(k,k+len(vs))))
    if uv is None:
        u0,v0,u1,v1=TILES[tile];uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)]
    b['uv'].append(uv)
def original_x(s):return 28*math.sin(s/240)+10*math.sin(s/90)
LOOP_X=original_x(LOOP_START)
def road_x(s):
    start=ROUTE['transitionStart']
    if s<=start:return original_x(s)
    if s>=LOOP_START:return LOOP_X
    t=(s-start)/(LOOP_START-start);w=t*t*t*(10+t*(-15+6*t))
    return original_x(s)*(1-w)+LOOP_X*w
def road_slope(s):
    start=ROUTE['transitionStart'];d=28/240*math.cos(s/240)+10/90*math.cos(s/90)
    if s<=start:return d
    if s>=LOOP_START:return 0
    length=LOOP_START-start;t=(s-start)/length;w=t*t*t*(10+t*(-15+6*t));dw=30*t*t*(1-t)*(1-t)/length
    return d*(1-w)+(LOOP_X-original_x(s))*dw
def basis(s):
    d=road_slope(s);n=math.sqrt(1+d*d)
    return Vector((1/n,-d/n,0)),Vector((d/n,1/n,0))
def pos(s,side=0,z=0):
    r,f=basis(s);return Vector((road_x(s),s,z))+r*side
def box(c,sz,mat='Architectural metal',tile='metal',angle=0):
    c=Vector(c);hx,hy,hz=[v/2 for v in sz];ca=math.cos(angle);sa=math.sin(angle)
    def p(x,y,z):return tuple(c+Vector((x*ca-y*sa,x*sa+y*ca,z)))
    v=[p(x,y,z) for z in (-hz,hz) for y in (-hy,hy) for x in (-hx,hx)]
    for ids in [(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)]:quad([v[i] for i in ids],mat,tile)
def beam(a,b,width,mat='Architectural metal',tile='metal'):
    a=Vector(a);b=Vector(b);along=(b-a).normalized();up=Vector((0,0,1))
    if abs(along.dot(up))>.97:up=Vector((0,1,0))
    u=along.cross(up).normalized()*width/2;v=along.cross(u).normalized()*width/2
    points=[a-u-v,a+u-v,a+u+v,a-u+v,b-u-v,b+u-v,b+u+v,b-u+v]
    for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:quad([tuple(points[i]) for i in ids],mat,tile)
def cylinder(c,r,h,mat='Architectural metal',tile='metal',count=10):
    c=Vector(c)
    for i in range(count):
        a=i*2*math.pi/count;b=(i+1)*2*math.pi/count
        q=[c+Vector((r*math.cos(a),r*math.sin(a),-h/2)),c+Vector((r*math.cos(b),r*math.sin(b),-h/2)),c+Vector((r*math.cos(b),r*math.sin(b),h/2)),c+Vector((r*math.cos(a),r*math.sin(a),h/2))]
        quad([tuple(v) for v in q],mat,tile)
    for z,reverse in [(-h/2,True),(h/2,False)]:
        pts=[tuple(c+Vector((r*math.cos(i*2*math.pi/count),r*math.sin(i*2*math.pi/count),z))) for i in range(count)]
        if reverse:pts.reverse()
        u0,v0,u1,v1=TILES[tile];uv=[((u0+u1)/2+math.cos(i*2*math.pi/count)*(u1-u0)/2,(v0+v1)/2+math.sin(i*2*math.pi/count)*(v1-v0)/2) for i in range(count)]
        quad(pts,mat,tile,uv)
def wall(c,width,height,tangent,normal,variant=0):
    c=Vector(c);u=Vector(tangent);n=Vector(normal);tile='glass' if variant==0 else 'concrete';mat='Office windows' if variant==0 else 'Concrete facade'
    nx=max(1,round(width/12));nz=max(1,round(height/24))
    for x in range(nx):
        for z in range(nz):
            p=c+u*(width*(x/nx-.5))+Vector((0,0,height*z/nz))+n*.045
            w=width/nx;h=height/nz
            quad([tuple(p),tuple(p+u*w),tuple(p+u*w+Vector((0,0,h))),tuple(p+Vector((0,0,h)))],mat,tile)
def tower(s,side,width,depth,height,variant=0,detail=True):
    r,f=basis(s);c=pos(s,side,0);angle=math.atan2(r.y,r.x)
    def local(x,y,z):return c+r*x+f*y+Vector((0,0,z))
    # Three-dimensional base, glazed floors, tiered crown and solid roofs.
    base=6;podium=min(height*.50,26);tiers=[(width,depth,base,podium),(width*.84,depth*.87,podium,height-7)]
    box(local(0,0,base/2),(width+1,depth+1,base),'Architectural metal','metal',angle)
    for tw,td,z0,z1 in tiers:
        if z1<=z0:continue
        box(local(0,0,(z0+z1)/2),(tw,td,z1-z0),'Architectural metal','metal',angle)
        for w,tang,norm,center in [(tw,r,-f,local(0,-td/2,z0)),(tw,-r,f,local(0,td/2,z0)),(td,f,r,local(tw/2,0,z0)),(td,-f,-r,local(-tw/2,0,z0))]:wall(center,w,z1-z0,tang,norm,variant)
        for z in range(round(z0),round(z1)+1,4 if detail else 12):box(local(0,0,z),(tw+.45,td+.45,.22),'Architectural metal','metal',angle)
        if detail:
            for x in [-tw/2,0,tw/2]:
                for y in [-td/2-.12,td/2+.12]:box(local(x,y,(z0+z1)/2),(.3,.34,z1-z0),'Concrete paving','paving',angle)
            for y in [-td/2,td/2]:
                for x in [-tw/2-.12,tw/2+.12]:box(local(x,y,(z0+z1)/2),(.34,.3,z1-z0),'Concrete paving','paving',angle)
    box(local(0,0,height-5),(width*.86,depth*.89,1.2),'Architectural metal','metal',angle)
    box(local(0,0,height-3),(width*.48,depth*.58,4),'Architectural metal','metal',angle)
    for x in (-width*.22,width*.22):
        box(local(x,0,height-.8),(2.8,4.5,2),'Architectural metal','metal',angle)
        cylinder(local(x,.5,height+.3),1.1,.45,count=10)
    beam(local(width*.14,0,height),local(width*.14,0,height+9),.16)
    box(local(width*.14,0,height+9),(.3,.3,.5),'Illuminated details','p1')
    if variant==0 and height>65:
        for x in [-width*.42,width*.42]:box(local(x,-depth*.435-.1,height*.65),(.12,.15,height*.48),'Illuminated details','p0',angle)
    # Street-level glass shops, overhang, entrance pillars and sign panels.
    if detail:
        facing=-1 if side>0 else 1
        wall(local(facing*(width/2+.6),0,.5),depth,4.7,f,r*facing,1)
        box(local(facing*(width/2+1),0,5.5),(2,depth+1,.45),'Concrete paving','paving',angle)
        for y in (-depth*.38,0,depth*.38):box(local(facing*(width/2+1),y,2.9),(.7,.7,5.8),'Concrete paving','paving',angle)
        if random.random()<.45:
            x=facing*(width/2+.5);box(local(x,-depth*.28,13),(.3,1.5,6),'Illuminated details','p1',angle)
            for j in range(4):box(local(x+facing*.05,-depth*.28,11+j),(.33,1.2,.13),'Painted details','p3',angle)

def skybridge(s):
    r,f=basis(s);c=pos(s,0,22);angle=math.atan2(r.y,r.x)
    def p(x,y,z):return c+r*x+f*y+Vector((0,0,z))
    box(p(0,0,0),(39,5.2,1),'Architectural metal','metal',angle)
    box(p(0,0,5.2),(39,5.5,.7),'Architectural metal','metal',angle)
    for side in (-1,1):
        box(p(side*18.2,0,-11),(1.8,5,22),'Concrete paving','paving',angle)
        wall(p(0,side*2.6,.6),36,4,r,f*side,0)
        box(p(0,side*2.9,5.5),(38,.13,.12),'Illuminated details','p0',angle)
        for x in range(-18,19,3):beam(p(x,side*2.75,.4),p(x,side*2.75,4.9),.17)
        for x in range(-18,18,6):beam(p(x,side*2.85,.5),p(x+6,side*2.85,4.8),.32)
    for x in range(-15,16,5):beam(p(x,-2.6,-.8),p(x,2.6,-.8),.4)

print('BUILDING_CITY',flush=True)
for ci in range(STORY_CHUNKS+ROUTE['loopVariants']):
    is_loop=ci>=STORY_CHUNKS
    chunk=f'boss_{ci-STORY_CHUNKS:02d}' if is_loop else f'city_{ci:02d}'
    s0=ci*CHUNK_LENGTH
    # Textured ground continues beneath buildings and cross-street gaps.
    for s in range(s0,s0+CHUNK_LENGTH,30):
        for lateral in range(-200,200,20):
            q=[pos(s,lateral,-.06),pos(s,lateral+20,-.06),pos(s+30,lateral+20,-.06),pos(s+30,lateral,-.06)]
            quad([tuple(p) for p in q],'Concrete paving','paving')
    # Road ribbons follow the same continuous path used by the game camera.
    for s in range(s0,s0+CHUNK_LENGTH,6):
        q=[pos(s,-12,.025),pos(s,12,.025),pos(s+6,12,.025),pos(s+6,-12,.025)]
        quad([tuple(p) for p in q],'Road asphalt','road',[(0,0),(1,0),(1,.26),(0,.26)])
        for sign in (-1,1):
            for a,b in [(12,17.5),(17.5,20)]:
                q=[pos(s,sign*a,.27),pos(s,sign*b,.27),pos(s+6,sign*b,.27),pos(s+6,sign*a,.27)]
                quad([tuple(p) for p in q],'Concrete paving','paving')
            beam(pos(s,sign*12,.16),pos(s+6,sign*12,.16),.26,'Concrete paving','paving')
            beam(pos(s,sign*12.5,.29),pos(s+6,sign*12.5,.29),.075,'Illuminated details','p0')
        for lane in (-8,-4,0,4,8):
            if (s//6)%2==0:
                beam(pos(s,lane,.035),pos(s+3,lane,.035),.075,'Painted details','p3')
    for s in range(s0+10,s0+CHUNK_LENGTH,30):
        for sign in (-1,1):
            c=pos(s,sign*14.5,0);r,f=basis(s)
            beam(c+Vector((0,0,.3)),c+Vector((0,0,6.5)),.13)
            beam(c+Vector((0,0,6.5)),c-r*sign*1.4+Vector((0,0,6.7)),.12)
            box(c-r*sign*1.2+Vector((0,0,6.65)),(.7,.35,.09),'Illuminated details','p2')
            for k in (0,7,14):cylinder(pos(s+k,sign*13.2,.85),.13,1.2,'Architectural metal','metal',count=6)
            box(pos(s+10,sign*16.5,.7),(1.6,4,1),'Concrete paving','paving')
            # Three-dimensional angular foliage in low concrete planters.
            for j in range(4):box(pos(s+8.6+j,sign*16.5,1.45),(.9,.95,.75),'Painted details','p4',j*.4)
    for s in range(s0+22,s0+CHUNK_LENGTH,43):
        for sign in (-1,1):
            w=random.uniform(15,24);d=random.uniform(26,36);h=random.choice([42,54,68,84,108,128])
            tower(s,sign*(20+w/2),w,d,h,random.randrange(2),True)
    for s in range(s0+45,s0+CHUNK_LENGTH,85):
        for sign in (-1,1):tower(s,sign*73,random.uniform(24,38),38,random.uniform(90,185),0,False)
    if ci in [0,3,6,8] or (is_loop and (ci-STORY_CHUNKS)%2==0):skybridge(s0+125)
    # Raised utilities make the later section visibly different from the entry.
    if ci in [4,5,6]:
        for s in range(s0,s0+CHUNK_LENGTH,18):
            r,f=basis(s);ang=math.atan2(r.y,r.x)
            box(pos(s,0,31),(34,18,.65),'Architectural metal','metal',ang)
            for sign in (-1,1):box(pos(s,sign*16,15),(1.1,1.4,30),'Concrete paving','paving',ang)
            for off in (-8,8):beam(pos(s,off,30.5),pos(s+18,off,30.5),.09,'Illuminated details','p0')

# Keep the flight corridor open. A flank spire punctuates each 720 m cycle.
chunk='boss_01';tower(LOOP_START+CHUNK_LENGTH+90,115,46,46,245,0,False)

# Normalize loop geometry to local coordinates so chunks can move without
# rebuilding meshes. Road, pavement and lane markings share identical ends.
for (name,mat),bucket in BUCKET.items():
    if name.startswith('boss_'):
        s0=LOOP_START+int(name.split('_')[1])*CHUNK_LENGTH
        bucket['v']=[(v[0]-LOOP_X,v[1]-s0,v[2]) for v in bucket['v']]

def make_objects():
    roots={};objects=[]
    for (name,mat),b in BUCKET.items():
        if name not in roots:
            root=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(root);roots[name]=root
        me=bpy.data.meshes.new(name+'_'+mat);me.from_pydata(b['v'],[],b['f']);me.materials.append(M[mat]);me.update()
        uv=me.uv_layers.new(name='UVMap')
        for p,coords in zip(me.polygons,b['uv']):
            for li,co in zip(p.loop_indices,coords):uv.data[li].uv=co
        ob=bpy.data.objects.new(name+'_'+mat,me);bpy.context.collection.objects.link(ob);ob.parent=roots[name]
        # Explicit geometry UVs and textures survive the glTF export.
        objects.append(ob)
    return roots,objects
roots,objects=make_objects();city_objects=list(objects)+list(roots.values())
for name,root in roots.items():
    if name.startswith('boss_'):
        root.location=(LOOP_X,LOOP_START+int(name.split('_')[1])*CHUNK_LENGTH,0)
        root['loop_length']=CHUNK_LENGTH
def export(path,obs):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_extras=True)
export(AS/'night-city.glb',city_objects)

# Enemy meshes are built with the same actual metal textures, not simple icons.
BUCKET={};chunk='scout'
box((0,0,0),(1.65,2.4,.55));box((0,-.55,.28),(.65,1,.35),'Painted details','p5')
for side in (-1,1):
    beam((side*.55,.4,0),(side*2,-.35,-.15),.36)
    box((side*1.8,-.1,-.12),(.5,1.9,.22),'Painted details','p5')
    box((side*.8,-1.05,-.05),(.35,.16,.22),'Illuminated details','p1')
box((0,1.22,0),(.62,.09,.25),'Illuminated details','p7')
chunk='interceptor'
box((0,0,0),(1.1,3.8,.55));box((0,.6,.3),(.6,1.4,.2),'Painted details','p5')
for side in (-1,1):
    quad([(side*.45,1,0),(side*3,-1.2,0),(side*2.2,-1.8,.15),(side*.45,-1.1,.25)],'Architectural metal','metal')
    beam((side*2.7,-1.1,.02),(side*2.15,-1.6,.1),.12,'Illuminated details','p7')
    box((side*.55,-1.7,0),(.26,.1,.2),'Illuminated details','p1')
chunk='turret'
cylinder((0,0,.4),1.35,.8,count=12);box((0,0,1.2),(1.8,1.8,1.1),'Painted details','p4')
for side in (-1,1):beam((side*.55,0,1.45),(side*.55,2.2,1.5),.26)
box((0,1,1.25),(.55,.1,.35),'Illuminated details','p7')
chunk='sentinel_body'
box((0,0,4.5),(8,7,3),'Painted details','p4');box((0,1,6.3),(5.4,5,1.2),'Painted details','p4')
box((0,3.6,4.8),(2.4,.2,1.5),'Architectural metal','metal')
box((0,3.75,4.8),(1.5,.15,.6),'Illuminated details','p0')
for side in (-1,1):
    box((side*4.6,.4,4.8),(2,5.2,2.3),'Painted details','p4')
    for j in range(3):beam((side*4.6,-.5+j*.65,5.6),(side*4.6,4+j*.2,5.8),.38)
    box((side*4.7,3.05,4.9),(1.2,.12,1),'Illuminated details','p1')
    for j in range(4):box((side*3.4,-2+j*1.3,6.2),(.4,.7,.35),'Architectural metal','metal')
for i in range(4):
    chunk='sentinel_leg_'+str(i);side=-1 if i<2 else 1;y=-2.2 if i%2==0 else 2.2
    beam((side*3.5,y,4.2),(side*5,y+.7,2),1,'Painted details','p4')
    beam((side*5,y+.7,2),(side*5.5,y-.3,.5),.65)
    box((side*5.5,y,.35),(1.8,2.8,.7),'Painted details','p4')
eroots,eobjects=make_objects();export(AS/'enemy-kit.glb',eobjects+list(eroots.values()))
for ob in eobjects+list(eroots.values()):bpy.data.objects.remove(ob,do_unlink=True)

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.world=bpy.data.worlds.new('Midnight');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.055,.13,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=1
bpy.ops.object.light_add(type='SUN',location=(-50,-80,140));sun=bpy.context.object;sun.rotation_euler=(math.radians(24),math.radians(-30),math.radians(-24));sun.data.energy=2.3;sun.data.color=(.38,.57,1);sun.data.angle=.3
bpy.ops.object.light_add(type='AREA',location=(0,-20,45));fill=bpy.context.object;fill.data.energy=16000;fill.data.shape='DISK';fill.data.size=80;fill.data.color=(.48,.66,1)
bpy.ops.object.camera_add(location=pos(14,0,8));cam=bpy.context.object;cam.rotation_euler=(pos(160,0,11)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=23;cam.data.clip_end=2600;scene.camera=cam
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'night-city.blend'))
scene.render.filepath=str(OUT/'concept-match.png');bpy.ops.render.render(write_still=True)
stats={'city_meshes':len(objects),'city_triangles':sum(len(o.data.loop_triangles) if o.data.loop_triangles else sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),
 'chunks':len(roots),'material_names':list(M),'textures':[im.name for im in (atlas,roadim,palette)],'all_meshes_uv_mapped':all(o.data.uv_layers for o in objects),'approach_length_m':LOOP_START,'loop_length_m':CHUNK_LENGTH*ROUTE['loopVariants'],
 'route_samples':[{'s':s,'x':road_x(s),'slope':road_slope(s)} for s in range(0,2521,12)]}
(OUT/'manifest.json').write_text(json.dumps(stats,indent=2),encoding='utf-8');print('CITY_COMPLETE',json.dumps({k:v for k,v in stats.items() if k!='route_samples'}),flush=True)
