"""Build the approved anime android prototype, bake textures, rig, export and render.
Run with Blender 4.5.13. All geometry is authored here; face paint is image-generated.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

P = argparse.ArgumentParser()
P.add_argument('--output', required=True)
P.add_argument('--skip-render', action='store_true')
A = P.parse_args(sys.argv[sys.argv.index('--') + 1:])
ROOT = Path(__file__).resolve().parents[1]
OUT = Path(A.output).resolve()
OUT.mkdir(parents=True, exist_ok=False)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
S = bpy.context.scene
S.unit_settings.system = 'METRIC'
S.render.engine = 'CYCLES'
S.cycles.device = 'CPU'
S.cycles.samples = 24
S.cycles.use_denoising = True
PARTS = []
BIND = {}
GLOW = {}


def mat(name, color, glow=0, painted=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    bs = n.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = .68
    GLOW[m.name] = tuple(c * glow for c in color)
    if painted:
        uv = n.new('ShaderNodeUVMap')
        uv.uv_map = 'UVMap'
        sep = n.new('ShaderNodeSeparateXYZ')
        l.new(uv.outputs['UV'], sep.inputs[0])
        wave = n.new('ShaderNodeMath')
        wave.operation = 'MULTIPLY'
        wave.inputs[1].default_value = 24
        l.new(sep.outputs['X'], wave.inputs[0])
        sin = n.new('ShaderNodeMath')
        sin.operation = 'SINE'
        l.new(wave.outputs[0], sin.inputs[0])
        ramp = n.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .08
        ramp.color_ramp.elements[0].color = (*(c*.65 for c in color), 1)
        ramp.color_ramp.elements[1].position = .85
        ramp.color_ramp.elements[1].color = (*color, 1)
        if name.startswith('Hair'):
            ramp.color_ramp.elements[0].position = 0
            ramp.color_ramp.elements[1].position = .48
            last = ramp.color_ramp.elements.new(1)
            last.color = (*(c*.75 for c in color), 1)
            l.new(sep.outputs['X'], ramp.inputs[0])
        else:
            l.new(sin.outputs[0], ramp.inputs[0])
        l.new(ramp.outputs[0], bs.inputs['Base Color'])
    return m


white = mat('Ceramic white', (.68,.75,.84))
edge = mat('Ceramic shade', (.32,.39,.49))
dark = mat('Graphite joints', (.026,.035,.057))
cloth = mat('Bodysuit', (.048,.065,.098), painted=True)
metal = mat('Mechanism', (.12,.17,.24))
skin = mat('Synthetic skin', (.82,.56,.43))
hair = mat('Hair', (.45,.29,.69), painted=True)
hair_light = mat('Hair highlight', (.62,.44,.83), painted=True)
purple = mat('Violet energy', (.47,.10,.95), glow=.9)
cyan = mat('Cyan energy', (.05,.70,.94), glow=.8)
face = mat('Painted anime face', (.82,.56,.43))
face_img = bpy.data.images.load(str(ROOT/'references/player/face-paint-v01.png'))
nodes, links = face.node_tree.nodes, face.node_tree.links
uvn = nodes.new('ShaderNodeUVMap')
uvn.uv_map = 'UVMap'
tex = nodes.new('ShaderNodeTexImage')
tex.image = face_img
tex.extension = 'EXTEND'
links.new(uvn.outputs[0], tex.inputs[0])
links.new(tex.outputs['Color'], nodes.get('Principled BSDF').inputs['Base Color'])


def mesh(name, verts, faces, material, bone='Spine', uv=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(material)
    me.update()
    ob = bpy.data.objects.new(name, me)
    S.collection.objects.link(ob)
    layer = me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        p.use_smooth = smooth
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            layer.data[li].uv = uv(co) if uv else (co.x*2+.5, co.z)
    # Recalculate normals before baking and exporting.
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.select_set(False)
    PARTS.append(ob)
    BIND[ob.name] = bone
    return ob


def loft(name, rings, material, bone='Spine', sides=10, smooth=False):
    # Rings: center x,y,z and ellipse radius x,y; all cross sections horizontal.
    vs = [(x+rx*math.sin(2*math.pi*i/sides), y-ry*math.cos(2*math.pi*i/sides), z)
          for x,y,z,rx,ry in rings for i in range(sides)]
    fs = [tuple(reversed(range(sides)))]
    for r in range(len(rings)-1):
        for i in range(sides):
            a = r*sides+i
            b = r*sides+(i+1)%sides
            fs.append((a,b,b+sides,a+sides))
    fs.append(tuple((len(rings)-1)*sides+i for i in range(sides)))
    return mesh(name, vs, fs, material, bone, smooth=smooth)


def beam(name, start, end, radii, material, bone='Spine', sides=8, smooth=False):
    start, end = Vector(start), Vector(end)
    direction = (end-start).normalized()
    ref = Vector((0,1,0))
    if abs(direction.dot(ref))>.95:
        ref = Vector((1,0,0))
    u = direction.cross(ref).normalized()
    v = direction.cross(u).normalized()
    vs = []
    for t, rx, ry in radii:
        for i in range(sides):
            ang = i*2*math.pi/sides
            co = start.lerp(end,t)+u*(rx*math.cos(ang))+v*(ry*math.sin(ang))
            vs.append(co)
    fs = [tuple(reversed(range(sides)))]
    for r in range(len(radii)-1):
        for i in range(sides):
            a = r*sides+i
            b = r*sides+(i+1)%sides
            fs.append((a,b,b+sides,a+sides))
    fs.append(tuple((len(radii)-1)*sides+i for i in range(sides)))
    return mesh(name, vs, fs, material, bone, smooth=smooth)


def box(name, loc, scale, material, bone='Spine', bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    if bevel:
        mod = ob.modifiers.new('Armor edge', 'BEVEL')
        mod.width = bevel
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.data.uv_layers.active.name = 'UVMap'
    PARTS.append(ob)
    BIND[ob.name] = bone
    ob.select_set(False)
    return ob


def plate(name, contour, depth, material, bone='Spine'):
    n = len(contour)
    vs = list(contour)+[(x,y+depth,z) for x,y,z in contour]
    fs = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    fs += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,material,bone)


def joint(name, loc, radius, bone):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=radius, location=loc)
    ob=bpy.context.object
    ob.name=name
    ob.data.materials.append(dark)
    ob.data.uv_layers.active.name='UVMap'
    for p in ob.data.polygons:
        p.use_smooth=True
    PARTS.append(ob)
    BIND[name]=bone
    ob.select_set(False)


# Torso and hip silhouette. Coordinates: X right, -Y front, Z up; meters.
loft('Flexible torso',[(0,0,.93,.14,.078),(0,0,1.02,.12,.070),
     (0,0,1.13,.105,.065),(0,0,1.23,.14,.083),(0,0,1.34,.175,.071)],cloth)
loft('Pelvis',[(0,0,.84,.10,.07),(0,0,.96,.145,.087),(0,0,1.025,.125,.074)],dark,'Hips')
loft('Neck',[(0,0,1.32,.052,.05),(0,0,1.49,.049,.045)],skin,'Head',sides=10,smooth=True)
loft('High collar',[(0,0,1.33,.060,.052),(0,0,1.42,.055,.05)],dark)
for side in (-1,1):
    plate('Chest ceramic',[(side*.012,-.10,1.29),(side*.125,-.103,1.32),
         (side*.17,-.10,1.25),(side*.12,-.124,1.20),(side*.025,-.111,1.23)],.033,white)
    plate('Rib armor',[(side*.105,-.064,1.17),(side*.147,-.071,1.20),
         (side*.129,-.077,1.08),(side*.095,-.075,1.05)],.035,edge)
    plate('Abdomen seam',[(side*.051,-.068,1.20),(side*.056,-.072,1.19),
         (side*.045,-.072,1.08),(side*.040,-.070,1.10)],.003,metal)
plate('Chest energy setting',[(0,-.128,1.30),(-.029,-.128,1.276),(0,-.133,1.248),(.029,-.128,1.276)],.012,metal)
plate('Chest energy',[(0,-.143,1.292),(-.018,-.143,1.276),(0,-.145,1.260),(.018,-.143,1.276)],.002,purple)
box('Waist belt',(0,0,1.015),(.275,.169,.038),metal,'Hips')

# Head has a projected front UV for the image-painted facial features.
head=loft('Head',[(0,0,1.472,.025,.024),(0,-.004,1.491,.067,.059),
    (0,0,1.525,.103,.081),(0,.006,1.581,.118,.086),
    (0,.009,1.640,.120,.091),(0,.018,1.697,.101,.080),
    (0,.02,1.737,.054,.049),(0,.02,1.75,.005,.005)],skin,'Head',sides=16,smooth=True)
head.data.materials.append(face)
for p in head.data.polygons:
    coords=[head.data.vertices[v].co for v in p.vertices]
    if sum(c.y for c in coords)/len(coords)<-.025:
        p.material_index=1
    for li in p.loop_indices:
        co=head.data.vertices[head.data.loops[li].vertex_index].co
        head.data.uv_layers['UVMap'].data[li].uv=(.5+co.x/.255,(co.z-1.417)/.326)
# A small physical nose, deliberately subtle from the game camera.
plate('Nose', [(-.005,-.079,1.561),(0,-.092,1.552),(.005,-.079,1.561),(0,-.082,1.58)],.003,skin,'Head')


def lock(name, centers, widths, thickness, material=hair):
    # A curved solid lens-shaped hair lock with a center ridge, six vertices per ring.
    vs=[]
    for (x,y,z),w in zip(centers,widths):
        vs.extend([(x-w,y,z),(x-w*.42,y-thickness*.9,z),
                   (x+w*.35,y-thickness,z),(x+w,y,z),
                   (x+w*.35,y+thickness*.38,z),(x-w*.35,y+thickness*.38,z)])
    fs=[tuple(reversed(range(6)))]
    for r in range(len(centers)-1):
        for i in range(6):
            a=r*6+i;b=r*6+(i+1)%6
            fs.append((a,b,b+6,a+6))
    fs.append(tuple((len(centers)-1)*6+i for i in range(6)))
    ob=mesh(name,vs,fs,material,'Hair',smooth=True)
    # Consistent lengthwise painted streaks per lock.
    for p in ob.data.polygons:
        for li in p.loop_indices:
            idx=ob.data.loops[li].vertex_index
            ob.data.uv_layers['UVMap'].data[li].uv=((idx%6)/5,(idx//6)/max(1,len(centers)-1))
    return ob

# Crown cap with a high forehead opening; the bangs overlap the seam.
vs=[]
cap_n=16
for r in range(4):
    for i in range(cap_n):
        a=2*math.pi*i/cap_n
        radii=[.008,.080,.125,.131]
        z=[1.771,1.747,1.697,1.56+.10*max(0,math.cos(a))][r]
        vs.append((radii[r]*math.sin(a),.018-radii[r]*.80*math.cos(a),z))
fs=[]
for r in range(3):
    for i in range(cap_n):
        a=r*cap_n+i;b=r*cap_n+(i+1)%cap_n
        fs.append((a,b,b+cap_n,a+cap_n))
mesh('Hair crown',vs,fs,hair_light,'Head',smooth=True)
for i in range(5):
    x=(i-2)*.044
    end_z=1.633+(.014 if i%2 else 0)
    lock(f'Fringe {i}',[(x*.6,-.052,1.735),(x,-.090,1.696),
         (x*1.04+.007,-.105,1.658),(x*1.08+.012,-.102,end_z)],
         [.03,.034,.027,.001],.007,hair_light)
for side in (-1,1):
    lock('Face framing lock',[(side*.099,-.052,1.697),(side*.12,-.067,1.58),
         (side*.126,-.058,1.45),(side*.164,-.045,1.391)],
         [.027,.032,.029,.001],.019,hair_light)
# Swept resting back hair, longest to character's left; central pack remains visible.
for i in range(8):
    x=(i-3.5)*.029
    sweep=.09+.065*(i/7)
    end_z=1.03+.19*(i/7)
    lock(f'Long back lock {i}',[(x*.55,.092,1.748),(x*.95,.126,1.66),
         (x*1.15,.140,1.52),(x*1.08,.156,1.37),(x+sweep*.60,.18,1.23),
         (x+sweep,.146,end_z)], [.024,.033,.036,.034,.03,.001],.020,hair if i%2 else hair_light)

# Mechanical headset with two triangular communication fins.
for side in (-1,1):
    beam('Headset outer',(side*.126,.006,1.652),(side*.155,.006,1.652),
         [(0,.055,.055),(1,.051,.051)],dark,'Head',sides=12)
    beam('Headset violet inset',(side*.156,.006,1.652),(side*.160,.006,1.652),
         [(0,.035,.035),(1,.031,.031)],purple,'Head',sides=12)
    beam('Headset center',(side*.161,.006,1.652),(side*.164,.006,1.652),
         [(0,.025,.025),(1,.025,.025)],dark,'Head',sides=10)
    plate('Communication fin',[(side*.113,-.005,1.69),(side*.135,-.005,1.825),
         (side*.180,-.005,1.731),(side*.164,-.005,1.68)],.025,white,'Head')
    plate('Fin dark insert',[(side*.131,-.009,1.710),(side*.137,-.009,1.789),
         (side*.164,-.009,1.733),(side*.155,-.009,1.710)],.005,dark,'Head')

for side, suffix in ((-1,'L'),(1,'R')):
    # Rigid armor surrounds small flexible joints. Bone lengths match the armor.
    upper=f'UpperArm.{suffix}'; fore=f'Forearm.{suffix}'; hand=f'Hand.{suffix}'
    thigh=f'Thigh.{suffix}'; shin=f'Shin.{suffix}'; foot=f'Foot.{suffix}'
    shoulder=(side*.20,0,1.32); elbow=(side*.29,0,1.105); wrist=(side*.377,-.012,.916)
    joint('Shoulder '+suffix,shoulder,.061,upper)
    beam('Upper arm core',shoulder,elbow,[(0,.043,.04),(1,.033,.033)],dark,upper)
    beam('Upper arm armor',Vector(shoulder).lerp(Vector(elbow),.18),Vector(shoulder).lerp(Vector(elbow),.81),
         [(0,.06,.052),(.5,.057,.05),(1,.042,.038)],white,upper)
    plate('Shoulder plate',[(side*.15,-.059,1.367),(side*.226,-.060,1.39),
         (side*.271,-.069,1.294),(side*.21,-.082,1.282)],.112,white,upper)
    box('Shoulder cyan',(side*.188,-.072,1.352),(.035,.012,.020),cyan,upper,bevel=.002)
    joint('Elbow '+suffix,elbow,.035,fore)
    beam('Forearm armor',Vector(elbow).lerp(Vector(wrist),.08),wrist,
         [(0,.042,.040),(.37,.052,.049),(1,.032,.032)],white,fore)
    box('Forearm indicator',(side*.332,-.055,1.043),(.028,.012,.041),cyan,fore,bevel=.004)
    beam('Wrist seal',Vector(elbow).lerp(Vector(wrist),.94),Vector(wrist)+Vector((side*.01,0,-.035)),
         [(0,.033,.033),(1,.029,.029)],dark,hand)
    beam('Glove',Vector(wrist)+Vector((side*.009,-.003,-.034)),Vector(wrist)+Vector((side*.034,-.006,-.10)),
         [(0,.032,.019),(1,.029,.018)],dark,hand)
    for finger in range(3):
        start=Vector(wrist)+Vector((side*(.018+.017*finger),-.005,-.094))
        beam('Finger',start,start+Vector((side*.016,-.004,-.035)),[(0,.008,.009),(1,.006,.007)],metal,hand,sides=5)
    # Long forearm-mounted weapon silhouette, projecting slightly past the hand.
    a=(side*.335,.035,1.105); b=(side*.483,.025,.794)
    beam('Arm weapon housing',a,b,[(0,.029,.035),(.18,.041,.045),(.84,.025,.033),(1,.01,.016)],dark,fore,sides=6)
    beam('Arm weapon ceramic',Vector(a)+Vector((side*.012,-.024,-.014)),Vector(b)+Vector((side*.014,-.027,.047)),
         [(0,.017,.014),(.65,.020,.013),(1,.004,.011)],white,fore,sides=5)
    beam('Arm weapon energy tip',b,Vector(b)+Vector((side*.027,-.001,-.067)),
         [(0,.017,.022),(1,.001,.002)],purple,fore,sides=6)
    # Legs.
    hx=side*.089; kx=side*.105
    beam('Upper thigh',(hx,0,.924),(kx,0,.777),[(0,.077,.075),(.4,.071,.072),(1,.061,.062)],skin,thigh,sides=10,smooth=True)
    beam('Thigh armor',(side*.100,0,.79),(kx,0,.592),[(0,.078,.078),(.5,.070,.073),(1,.064,.067)],white,thigh,sides=8)
    plate('Thigh top inset',[(side*.073,-.078,.783),(side*.13,-.078,.78),
         (side*.132,-.076,.744),(side*.076,-.077,.744)],.008,metal,thigh)
    joint('Knee '+suffix,(kx,0,.553),.057,shin)
    beam('Knee axle',(kx-.064,0,.553),(kx+.064,0,.553),[(0,.035,.035),(1,.035,.035)],metal,shin,sides=10)
    beam('Shin core',(kx,0,.545),(kx,.005,.15),[(0,.036,.037),(1,.031,.034)],dark,shin)
    loft('Shin boot',[(kx,.004,.145,.043,.046),(kx,.003,.26,.047,.050),
         (kx,.008,.40,.061,.060),(kx,0,.52,.061,.057)],white,shin,sides=8)
    plate('Knee front',[(kx-.04,-.061,.58),(kx+.04,-.061,.58),(kx+.029,-.077,.465),
         (kx,-.085,.438),(kx-.029,-.077,.465)],.024,dark,shin)
    box('Knee cyan marker',(kx,-.089,.548),(.017,.007,.024),cyan,shin,bevel=.002)
    plate('Shin central seam',[(kx-.007,-.058,.43),(kx+.007,-.058,.43),
         (kx+.006,-.047,.225),(kx-.006,-.047,.225)],.004,edge,shin)
    joint('Ankle '+suffix,(kx,0,.125),.039,foot)
    boot=box('Foot boot',(kx,-.036,.066),(.099,.192,.106),white,foot,bevel=.017)
    box('Boot sole',(kx,-.037,.019),(.107,.203,.031),dark,foot,bevel=.009)
    box('Toe violet edge',(kx,-.140,.03),(.083,.014,.019),purple,foot,bevel=.003)
    box('Foot upper joint',(kx,-.016,.121),(.059,.083,.031),metal,foot,bevel=.008)
    # White segmented skirt panels flare from a fitted belt.
    for front in (-1,1):
        for offset in (0,.076):
            x=side*(.035+offset)
            plate('Hip skirt plate',[(x-side*.032,front*.093,1.045),
                 (x+side*.032,front*.080,1.043),(x+side*.057,front*.128,.856),
                 (x-side*.040,front*.143,.868)],front*.017,white,'Hips')
    plate('Hip side panel',[(side*.131,-.053,1.033),(side*.138,.071,1.032),
         (side*.218,.083,.884),(side*.220,-.095,.871)],.015,edge,'Hips')
    # Twin downward-facing boost pods with open nozzles (flames are separate).
    tx=side*.244; ty=.071
    beam('Booster mount',(side*.138,.072,.973),(tx,.072,.899),[(0,.028,.030),(1,.034,.034)],metal,'Hips',sides=8)
    loft('Hip thruster',[(tx,ty,.702,.038,.039),(tx,ty,.745,.051,.052),
        (tx,ty,.842,.055,.057),(tx,ty,.914,.049,.051)],white,'Hips',sides=10)
    loft('Thruster violet collar',[(tx,ty,.842,.057,.059),(tx,ty,.881,.058,.060)],purple,'Hips',sides=10)
    loft('Thruster top fitting',[(tx,ty,.892,.053,.055),(tx,ty,.929,.049,.05)],dark,'Hips',sides=10)
    # Annular nozzle: outer and inner circles, open at the bottom.
    vs=[]
    for r,z in ((.041,.723),(.043,.682),(.032,.682),(.030,.723)):
        vs += [(tx+r*math.cos(i*2*math.pi/10),ty+r*math.sin(i*2*math.pi/10),z) for i in range(10)]
    fs=[]
    for ring in range(3):
        fs += [(ring*10+i,ring*10+(i+1)%10,(ring+1)*10+(i+1)%10,(ring+1)*10+i) for i in range(10)]
    mesh('Open thruster nozzle',vs,fs,dark,'Hips')
    loft('Nozzle interior glow',[(tx,ty,.720,.027,.027),(tx,ty,.724,.027,.027)],purple,'Hips',sides=10)

# Stacked rectangular back unit, extending behind the hair, like the source sprite.
box('Backpack core',(0,.134,1.212),(.142,.101,.292),dark)
box('Backpack side left',(-.08,.138,1.211),(.026,.085,.252),edge)
box('Backpack side right',(.08,.138,1.211),(.026,.085,.252),edge)
for i in range(5):
    z=1.318-i*.049
    box('Backpack stacked bar',(0,.190,z),(.121,.023,.030),metal)
    if i<3:
        box('Backpack energy bar',(0,.204,z+.005),(.095,.007,.016),purple if i%2==0 else cyan,bevel=.001)


def make_rig():
    ar=bpy.data.armatures.new('Player skeleton')
    rig=bpy.data.objects.new('Player_Rig',ar)
    S.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    def bone(name,h,t,parent=None):
        b=ar.edit_bones.new(name);b.head=h;b.tail=t
        if parent:b.parent=ar.edit_bones[parent]
    bone('Root',(0,0,0),(0,0,.15))
    bone('Hips',(0,0,.90),(0,0,1.07),'Root')
    bone('Spine',(0,0,1.07),(0,0,1.36),'Hips')
    bone('Head',(0,0,1.36),(0,0,1.75),'Spine')
    bone('Hair',(0,.09,1.64),(0,.14,1.23),'Head')
    for side,suf in ((-1,'L'),(1,'R')):
        bone('UpperArm.'+suf,(side*.20,0,1.32),(side*.29,0,1.105),'Spine')
        bone('Forearm.'+suf,(side*.29,0,1.105),(side*.377,-.012,.916),'UpperArm.'+suf)
        bone('Hand.'+suf,(side*.377,-.012,.916),(side*.41,-.015,.817),'Forearm.'+suf)
        bone('Thigh.'+suf,(side*.089,0,.924),(side*.105,0,.553),'Hips')
        bone('Shin.'+suf,(side*.105,0,.553),(side*.105,0,.125),'Thigh.'+suf)
        bone('Foot.'+suf,(side*.105,0,.125),(side*.105,-.12,.05),'Shin.'+suf)
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.select_set(False)
    rig.show_in_front=True
    return rig


rig=make_rig()
for ob in PARTS:
    group=ob.vertex_groups.new(name=BIND[ob.name])
    group.add(list(range(len(ob.data.vertices))),1,'REPLACE')
    ob.select_set(True)
bpy.context.view_layer.objects.active=PARTS[0]
bpy.ops.object.join()
body=bpy.context.object
body.name='Player_Mesh'
# Preserve source UVMap and bake a second, non-overlapping UV set.
body.data.uv_layers.new(name='GameUV')
body.data.uv_layers.active=body.data.uv_layers['GameUV']
body.data.uv_layers['GameUV'].active_render=True
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.015,area_weight=.2)
bpy.ops.object.mode_set(mode='OBJECT')
# Reserve a large contiguous atlas region for the face; tiny scattered islands
# would destroy the eyes and mouth even when the rest of the atlas is large.
source_uv=body.data.uv_layers['UVMap']
game_uv=body.data.uv_layers['GameUV']
for poly in body.data.polygons:
    is_face=body.data.materials[poly.material_index].name == face.name
    for li in poly.loop_indices:
        if is_face:
            u,v=source_uv.data[li].uv
            game_uv.data[li].uv=(.015+.42*u,.015+.42*v)
        else:
            u,v=game_uv.data[li].uv
            game_uv.data[li].uv=(.46+.53*u,.01+.98*v)
S.render.bake.use_pass_direct=False
S.render.bake.use_pass_indirect=False
S.render.bake.use_pass_color=True
S.render.bake.margin=6
S.cycles.samples=1
base=bpy.data.images.new('Player_BaseColor_2048',2048,2048,alpha=False)
emission=bpy.data.images.new('Player_Emission_512',512,512,alpha=False)
orig_links={}
for m in body.data.materials:
    n=m.node_tree.nodes;l=m.node_tree.links
    target=n.new('ShaderNodeTexImage');target.name='BAKE_TARGET';target.image=base;n.active=target
print('BAKING PAINTED BASE COLOR')
bpy.ops.object.bake(type='DIFFUSE')
base.filepath_raw=str(OUT/'player-basecolor.png');base.file_format='PNG';base.save()
for m in body.data.materials:
    n=m.node_tree.nodes;l=m.node_tree.links
    out=n.get('Material Output')
    orig_links[m.name]=out.inputs['Surface'].links[0].from_socket
    sh=n.new('ShaderNodeEmission');sh.name='BAKE_GLOW'
    sh.inputs[0].default_value=(*GLOW[m.name],1)
    l.new(sh.outputs[0],out.inputs['Surface'])
    n['BAKE_TARGET'].image=emission;n.active=n['BAKE_TARGET']
print('BAKING EMISSION MASK')
bpy.ops.object.bake(type='EMIT')
emission.filepath_raw=str(OUT/'player-emission.png');emission.file_format='PNG';emission.save()
final=bpy.data.materials.new('Player painted atlas')
final.use_nodes=True
n,l=final.node_tree.nodes,final.node_tree.links
bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.72
uv=n.new('ShaderNodeUVMap');uv.uv_map='GameUV'
bt=n.new('ShaderNodeTexImage');bt.image=base
et=n.new('ShaderNodeTexImage');et.image=emission
l.new(uv.outputs[0],bt.inputs[0]);l.new(uv.outputs[0],et.inputs[0])
l.new(bt.outputs['Color'],bs.inputs['Base Color'])
l.new(et.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.6
body.data.materials.clear();body.data.materials.append(final)
for p in body.data.polygons:p.material_index=0
# Remove the source mapping only after the paint has been baked.
body.data.uv_layers.remove(body.data.uv_layers['UVMap'])
body.data.uv_layers.active=body.data.uv_layers['GameUV']
mod=body.modifiers.new('Player rig','ARMATURE');mod.object=rig
body.parent=rig
base.pack();emission.pack()
face_img.pack()

# A short rigid-armor hover motion to inspect joints and rear silhouette.
S.render.fps=24
S.frame_start=1;S.frame_end=49
for frame in (1,13,25,37,49):
    phase=2*math.pi*(frame-1)/48
    for pb in rig.pose.bones:
        pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
    rig.pose.bones['Root'].location.z=.12+.015*math.sin(phase)
    rig.pose.bones['Spine'].rotation_euler.x=math.radians(5)
    rig.pose.bones['Thigh.L'].rotation_euler.x=math.radians(-14+2*math.sin(phase))
    rig.pose.bones['Shin.L'].rotation_euler.x=math.radians(31)
    rig.pose.bones['Thigh.R'].rotation_euler.x=math.radians(4)
    rig.pose.bones['Foot.R'].rotation_euler.x=math.radians(-9)
    rig.pose.bones['Hair'].rotation_euler.x=math.radians(3+2*math.sin(phase))
    rig.pose.bones['Hair'].rotation_euler.z=math.radians(2*math.cos(phase))
    for pb in rig.pose.bones:
        pb.keyframe_insert('rotation_euler',frame=frame,group=pb.name)
        if pb.name=='Root':pb.keyframe_insert('location',frame=frame,group=pb.name)
rig.animation_data.action.name='HoverIdle'
S.frame_set(1)
# GLB bind/rest pose remains the authored low A-pose; animation is optional.
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True);rig.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(OUT/'player.glb'),export_format='GLB',use_selection=True,
    export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_skins=True,
    export_def_bones=True,export_apply=False,export_cameras=False,export_lights=False)

# Neutral studio previews; stage objects are deliberately excluded from GLB.
rig.data.pose_position='REST'
S.cycles.samples=32
S.world.use_nodes=True
S.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.21,.28,1)
S.world.node_tree.nodes['Background'].inputs[1].default_value=.6
S.view_settings.view_transform='Standard'
S.view_settings.look='Medium High Contrast'
S.view_settings.exposure=-.35
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,energy,size in [('Key',(-3,-4,5),380,4),('Fill',(3,-1,3),210,3),('Rim',(1,3,4),400,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    light=bpy.context.object;light.name=name;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;aim(light,(0,0,1))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.006))
floor=bpy.context.object;floor.name='Preview floor'
floor.data.materials.append(mat('Studio floor',(.14,.17,.22)))
bpy.ops.object.camera_add(location=(2.7,-4,2.5))
cam=bpy.context.object;cam.name='Preview camera';cam.data.type='ORTHO';cam.data.ortho_scale=2.18;aim(cam,(0,0,.92));S.camera=cam
S.render.resolution_x=900;S.render.resolution_y=1050;S.render.resolution_percentage=100
S.render.image_settings.file_format='PNG'
if not A.skip_render:
    for name,location in [('front',(0,-5,.98)),('back',(0,5,.98)),('side',(5,0,.98)),('three-quarter',(2.7,-4,2.25))]:
        floor.hide_render=name!='three-quarter'
        cam.location=location;aim(cam,(0,0,.92))
        S.render.filepath=str(OUT/f'{name}.png');bpy.ops.render.render(write_still=True)
    rig.data.pose_position='POSE';S.frame_set(13)
    floor.hide_render=False
    cam.location=(-2,4,2.1);aim(cam,(0,0,1.03));S.render.filepath=str(OUT/'hover-back.png');bpy.ops.render.render(write_still=True)
rig.data.pose_position='POSE';S.frame_set(1)
cam.location=(2.7,-4,2.25);aim(cam,(0,0,.92))
# Default saved viewport is an uncluttered material-preview view of the character.
for ob in S.objects:ob.select_set(False)
body.select_set(True);bpy.context.view_layer.objects.active=body
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=2.7
            area.spaces.active.region_3d.view_location=(0,0,.96)
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'player.blend'))
body.data.calc_loop_triangles()
manifest={'blender':bpy.app.version_string,'triangles':len(body.data.loop_triangles),
    'vertices':len(body.data.vertices),'bones':len(rig.data.bones),'materials':1,
    'basecolor':[2048,2048],'emission':[512,512],'animation':'HoverIdle (2 seconds, 24 fps)',
    'height_m':1.825,'up_axis_blend':'Z','up_axis_glb':'Y','front_blend':'-Y',
    'notes':['Prototype rigid armor weighting; no facial rig or physics.',
             'Hair and armor detail baked; face uses generated paint.',
             'Exhaust effects and runtime game integration are not included.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('PLAYER COMPLETE',json.dumps(manifest))
