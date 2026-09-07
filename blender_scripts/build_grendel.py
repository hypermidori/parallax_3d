"""GRENDEL HOVER. Built from references/enemies/grendel/design-v01.png.
All surfaces use the generated image atlas. +Y is the firing direction.
Run: tools/blender.ps1 --background --factory-startup --python blender_scripts/build_grendel.py
"""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import painted_enemy_mesh as m
from build_support_enemies import tube
from mathutils import Vector

TILES={'armor':(.012,.512,.321,.988),'olive':(.345,.512,.654,.988),'ivory':(.679,.512,.988,.988),
 'metal':(.012,.012,.321,.488),'black':(.345,.012,.654,.488),
 'cyan':(.684,.393,.982,.478),'red':(.684,.268,.982,.352),
 'steel':(.684,.143,.982,.228),'hazard':(.684,.018,.982,.102)}
m.begin('Grendel',atlas='grendel-atlas.png',tiles=TILES,emissive=('red','cyan'))
for name in ['armor','olive','ivory']:
    shader=m.M[name].node_tree.nodes.get('Principled BSDF');shader.inputs['Metallic'].default_value=.24;shader.inputs['Roughness'].default_value=.68
for name,power in [('cyan',3.2),('red',1.8)]:
    m.M[name].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=power

rig={}
def rect(cx,cy,w,h,c=.13):
    x0,x1=cx-w/2,cx+w/2;y0,y1=cy-h/2,cy+h/2
    return [(x0+c,y0),(x1-c,y0),(x1,y0+c),(x1,y1-c),(x1-c,y1),(x0+c,y1),(x0,y1-c),(x0,y0+c)]

def plate(name,cx,y,z,w,h,mat='olive',slope=0):
    outline=rect(cx,y,w,h,min(w,h)*.13);n=len(outline)
    verts=[(x,yy,z+slope*(yy-y)+dz) for dz in [-.12,0] for x,yy in outline]
    return m.mesh(name,verts,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)], [mat,'metal'],[1,0]+[1]*n,.025)

def bolt(name,center,r=.075,axis='Z',mat='steel'):
    return m.cylinder(name,center,r,.045,mat,axis,8)

def optic(name,x,y,z,r=.22):
    m.ring(name+' square bezel',x,y,z,r*1.4,r*1.4,.14,'metal',r*.27)
    m.cylinder(name+' dark lens',(x,y-.04,z),r,.05,'black','Y',12)
    m.cylinder(name+' red lens',(x,y,z),r*.72,.025,'red','Y',12)
    m.cylinder(name+' pupil',(x,y+.02,z),r*.32,.026,'red','Y',12)

def hinge(name,position,r):
    # Joint axle points outwards; concentric rings make the folding mechanism legible.
    for offset,rr,mat in [(0,r,'black'),(.05,r*.83,'metal'),(.09,r*.58,'steel'),(.13,r*.28,'black')]:
        ob=m.cylinder(name+mat,(0,0,0),rr,.10,mat,'Z',12)
        ob.rotation_euler.y=math.pi/2;ob.location=Vector(position)+Vector((math.copysign(offset,position[0]),0,0))

# Central armored carapace, low nose and raised rear drive deck.
stations=[(-3.65,1.24,1.00,3.54),(-2.65,1.63,.68,4.00),(-.9,1.66,.58,3.96),(.9,1.50,.55,3.57),(2.40,1.17,.55,3.05),(3.72,.86,.67,2.55)]
m.loft('Central heavy carapace',stations,colors=('olive','armor','metal'))
m.loft('Lower floating chassis',[(-3.25,1.85,.40,1.25),(-1.9,2.0,.33,1.45),(1.5,1.8,.34,1.25),(3.42,1.03,.52,1.15)],colors=('metal','black','metal'))
for j,(y,z,w,h,slope) in enumerate([(-2.58,4.055,1.85,1.28,-.02),(-1.12,4.02,1.92,1.32,-.11),(.30,3.80,1.74,1.25,-.22),(1.58,3.40,1.37,1.11,-.34),(2.76,2.985,1.0,.92,-.37)]):
    plate('Central dorsal plate '+str(j),0,y,z,w,h,'olive',slope)
    for sx in [-1,1]:
        bolt('Dorsal locking stud',(sx*w*.37,y-.32,z+.015+slope*(-.32)),.048)
# Rear radiator bank sits within the raised deck rather than becoming a turret.
plate('Rear engine grille housing',0,-3.1,3.875,1.65,.78,'black')
for x in [-.63,-.42,-.21,0,.21,.42,.63]:
    m.beam('Rear radiator rib',(x,-3.43,3.905),(x,-2.79,3.905),.038,'metal',4)
for sx in [-1,1]:
    for j in range(3):
        m.slab('Rear coolant cartridge',rect(sx*1.0,-3.15+j*.28,.24,.21,.035),3.66,3.9,'metal','black',.015)

# Inset octagonal core, framed by thick cheek armor and lower chin.
for y,r,mat in [(3.77,.91,'metal'),(3.87,.78,'steel'),(3.93,.68,'black'),(3.966,.52,'red')]:
    m.cylinder('Central energy emitter '+mat,(0,y,1.78),r,.08,mat,'Y',8)
m.cylinder('Core bright pupil',(0,4.025,1.78),.27,.035,'red','Y',12)
for sx in [-1,1]:
    m.loft('Core side armor cheek',[(3.25,.22,.70,2.78),(4.04,.20,.91,2.50)],cx=sx*.89,colors=('olive','armor','metal'))
plate('Core chin plate',0,3.75,.835,1.35,.69,'armor',-.1)
for a in range(8):
    ang=(a+.5)*math.tau/8
    bolt('Emitter bezel bolt',(.81*math.cos(ang),3.925,1.78+.81*math.sin(ang)),.055,'Y')
m.anchor('ShotOrigin',(0,4.08,1.78))
m.anchor('AimTarget',(0,4.03,1.78))

# Twin long shoulder packs echo the original sprite's layered side carapace.
for sx in [-1,1]:
    x=sx*2.28
    m.loft('Long shoulder armored spine', [(-3.43,.64,.89,3.51),(-2.60,.85,.62,3.99),(-.70,.83,.55,3.92),(.15,.79,.52,3.54),(1.00,.88,.47,2.88),(2.78,.85,.45,2.50),(3.56,.65,.67,2.18)],cx=x,colors=('olive','armor','metal'))
    for j,(y,z,w,h,slope) in enumerate([(-2.50,4.055,1.04,1.07,0),(-1.35,4.02,1.01,1.08,-.08),(-.23,3.765,1.05,.86,-.43),(1.55,2.855,1.13,1.04,-.22),(2.65,2.63,1.05,.88,-.28)]):
        plate('Shoulder segmented cover',x,y,z,w,h,'armor' if j%2==0 else 'olive',slope)
    # Elevated rear sensor and low front sensor, as in the source boss.
    m.loft('Raised shoulder sensor housing',[(.01,.43,3.11,3.96),(.53,.39,3.11,3.89)],cx=x,colors=('armor','olive','metal'))
    optic('Upper shoulder sensor',x,.61,3.52,.235)
    optic('Lower shoulder sensor',x,3.59,1.22,.23)
    for y,z in [(.58,2.58),(.91,2.49)]:
        m.slab('Shoulder radiator bed',rect(x,y,1.07,.22,.03),z,z+.10,'black','metal',.015)
        for dx in [-.36,-.18,0,.18,.36]:
            m.panel('Shoulder vent fin',x+dx,y,z+.115,.07,.18,'steel')
    # Exposed chassis piping in the seams between center hull and shoulder packs.
    for y in [-2.75,-1.72,-.5,.7,1.7,2.6]:
        m.beam('Interplate hydraulic coupling',(sx*1.47,y,1.63),(sx*1.64,y,2.16),.12,'metal',8)
    plate('Shoulder identification tab',x,-2.45,4.08,.49,.20,'ivory')

# Four independent folded leg / hover pod assemblies. They are tucked and stabilized,
# never animated with alternating footfalls. Local joint pivots survive batching.
for sx in [-1,1]:
    for sy in [1,-1]:
        index=(0 if sx<0 else 2)+(0 if sy>0 else 1)
        name='FoldedLeg'+str(index);start=len(m.parts);x=sx*4.23;cy=sy*1.91
        m.beam(name+' hip cross-member',(sx*2.91,cy,2.03),(sx*4.28,cy,2.16),.28,'metal',8)
        # Pod shell takes the form of an armored hood with the folded limbs exposed below.
        m.loft(name+' shoulder pod',[(cy-1.63,.60,1.72,2.94),(cy-1.20,.98,1.49,3.39),(cy+.84,.98,1.77,3.14),(cy+1.48,.70,1.83,2.58)],cx=x,colors=('armor','olive','metal'))
        plate(name+' top access hatch',x,cy-.18,3.31,1.46,1.71,'armor',-.13)
        plate(name+' hazard strip',x,cy+1.11,2.97,1.19,.22,'hazard',-.85)
        # Front-facing small panel with painted identification and recessed border.
        m.ring(name+' front armor bezel',x,cy+1.50,2.23,.56,.28,.10,'olive',.055)
        # The Z-shaped folded leg sits along the outer face of the pod.
        outer=sx*5.12
        hip=(outer,cy-.75,1.98);knee=(outer,cy+.87,1.31);ankle=(outer,cy+.21,.71)
        for label,a,b,r in [('upper folded link',hip,knee,.25),('lower folded link',knee,ankle,.23)]:
            m.beam(name+label,a,b,r,'metal',8)
            m.beam(name+label+' armored spar',Vector(a)+Vector((sx*.05,0,.14)),Vector(b)+Vector((sx*.05,0,.14)),r*.62,'olive',6)
        m.beam(name+' piston sleeve',(sx*4.92,cy-.56,1.70),(sx*4.92,cy+.24,1.39),.135,'black',10)
        m.beam(name+' exposed piston',(sx*4.92,cy+.24,1.39),(sx*4.92,cy+.59,1.26),.078,'steel',10)
        for label,pos,r in [('hip',hip,.43),('knee',knee,.38),('ankle',ankle,.34)]:hinge(name+label,pos,r)
        m.loft(name+' tucked terminal pad',[(cy+.08,.60,.34,.93),(cy+.66,.71,.34,.92),(cy+1.16,.67,.39,.81)],cx=x,colors=('olive','metal','black'))
        for dx in [-.32,.32]:
            m.beam(name+' foot rib',(x+dx,cy+.15,.92),(x+dx,cy+1.05,.88),.055,'metal',6)
        for dx in [-.43,.43]:
            m.beam(name+' front folded shin',(x+dx,cy+1.0,1.69),(x+dx,cy+.87,.89),.15,'olive',8)
            m.cylinder(name+' front shin joint',(x+dx,cy+1.06,1.50),.19,.11,'metal','Y',12)
        # Downward engine collar is visibly attached to the folded terminal pad.
        m.cylinder(name+' downward thruster',(x,cy+.62,.31),.62,.30,'metal','Z',16)
        m.cylinder(name+' nozzle shadow',(x,cy+.62,.15),.51,.025,'black','Z',16)
        m.cylinder(name+' blue throat',(x,cy+.62,.12),.405,.024,'cyan','Z',16)
        for angle in range(8):
            a=angle*math.tau/8
            bolt(name+' nozzle rim',(x+.55*math.cos(a),cy+.62+.55*math.sin(a),.17),.038,'Z')
        rig[name]={'parts':m.parts[start:],'pivot':(sx*3.10,cy,2.05)}
        # Short textured luminous exhaust: independent scale pivot at the nozzle exit.
        jetstart=len(m.parts)
        m.cylinder('Hover plume '+str(index),(x,cy+.62,-.12),.15,.44,'cyan','Z',12,r2=.375)
        rig['HoverJet'+str(index)]={'parts':m.parts[jetstart:],'pivot':(x,cy+.62,.10)}
        m.anchor('HoverNozzle'+str(index),(x,cy+.62,.10))

m.finish('grendel-hover','Grendel Hover',target=(0,0,1.95),span=16,rig=rig)
