"""Two support enemies. Build after the generated design sheets and shared atlas exist."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import painted_enemy_mesh as m
from mathutils import Vector
def tube(name,cx,y,cz,outer,inner,length,mat='ivory',count=20):
    v=[]
    for yy,r in [(y,outer),(y,inner),(y-length,inner),(y-length,outer)]:
        for i in range(count):
            a=i*math.tau/count;v.append((cx+r*math.cos(a),yy,cz+r*math.sin(a)))
    f=[];fm=[]
    for i in range(count):
        j=(i+1)%count
        f.extend([(i,j,j+count,i+count),(i+count,j+count,j+count*2,i+count*2),(i,j,j+count*3,i+count*3)])
        fm.extend([0,1,2])
    return m.mesh(name,v,f,[mat,'black','metal'],fm,.008)
def stack(name,outline,levels,top='olive',side='olive'):
    n=len(outline);v=[(x*sx,y*sy,z) for z,sx,sy in levels for x,y in outline]
    f=[tuple(reversed(range(n)))];fm=[1]
    for k in range(len(levels)-1):
        for j in range(n):
            f.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j));fm.append(1)
    f.append(tuple(range(len(v)-n,len(v))));fm.append(0)
    return m.mesh(name,v,f,[top,side],fm,.015)
def disc(name,center,radius,depth,mat,axis='Y',count=16):
    return m.cylinder(name,center,radius,depth,mat,axis,count)
def firefly():
    m.begin('Firefly')
    m.loft('Rounded scout fuselage',[(-2.05,.28,-.18,.50),(-1.65,.58,-.33,.82),(-.7,.77,-.42,.99),(.55,.71,-.43,.81),(1.5,.55,-.32,.55),(2.02,.37,-.20,.40)],colors=('orange','ivory','metal'))
    for j,(y,z) in enumerate([(-1.35,.9),(-.7,1.02),(-.1,.96),(.5,.86),(1.06,.69)]):
        m.panel('Dorsal orange hatch '+str(j),0,y,z,.32,.42,'orange')
        m.panel('Dorsal dark inset '+str(j),0,y,z+.035,.14,.22,'black')
        if j<2:m.panel('Warm status strip '+str(j),0,y,z+.07,.11,.08,'amber')
    # One central shallow optical/energy core, never a cannon tube.
    for i,(y,r,mat) in enumerate([(2.025,.435,'metal'),(2.055,.365,'steel'),(2.08,.30,'black'),(2.105,.245,'amber')]):
        disc('Optical core '+str(i),(0,y,.12),r,.035,mat,count=20)
    disc('Optical inner aperture',(0,2.132,.12),.17,.015,'black',count=20)
    disc('Optical amber pupil',(0,2.145,.12),.125,.016,'amber',count=20)
    for i in range(8):
        a=i*math.tau/8
        disc('Optical bezel fastener',(math.cos(a)*.39,2.052,.12+math.sin(a)*.39),.022,.022,'steel',count=8)
    m.anchor('ShotOrigin',(0,2.159,.12))
    for sign in [-1,1]:
        label='Port' if sign<0 else 'Starboard';cx=sign*1.32
        m.slab(label+' shoulder coupling',[(sign*.65,-.65),(sign*1.35,-.6),(sign*1.4,.75),(sign*.68,1.05)],-.2,.42,'metal','metal',.04)
        disc(label+' graphite engine trunk',(cx,.1,.18),.58,2.5,'metal',count=20)
        # Curved orange armor follows the top half of the turbine casing.
        verts=[]
        for yy in [-1.10,1.20]:
            for i in range(11):
                a=i*math.pi/10;verts.append((cx+.60*math.cos(a),yy,.18+.60*math.sin(a)))
        m.mesh(label+' curved orange engine cowling',verts,[(i,i+1,i+12,i+11) for i in range(10)],['orange'])
        tube(label+' ivory intake ring',cx,1.52,.18,.635,.48,.28)
        tube(label+' intake black recess',cx,1.37,.18,.482,.445,.09,'black')
        disc(label+' intake backplate',(cx,1.345,.18),.445,.02,'black',count=20)
        for j in range(10):
            a=j*math.tau/10;ca,sa=math.cos(a),math.sin(a)
            def p(r,angle,y):
                return (cx+r*math.cos(a+angle),y,.18+r*math.sin(a+angle))
            m.mesh(label+' turbine blade '+str(j),[p(.13,0,1.395),p(.42,.03,1.40),p(.42,.28,1.425),p(.16,.35,1.445)],[(0,1,2,3)],['metal'])
        disc(label+' turbine hub',(cx,1.445,.18),.14,.10,'steel',count=12)
        disc(label+' hub dark bolt',(cx,1.505,.18),.065,.023,'black',count=10)
        tube(label+' rear exhaust collar',cx,-1.38,.18,.50,.34,-.18,'metal')
        disc(label+' rear exhaust shadow',(cx,-1.565,.18),.33,.02,'black',count=16)
        disc(label+' rear warm exhaust',(cx,-1.58,.18),.22,.024,'amber',count=16)
        wing=[(sign*1.70,-.65),(sign*2.31,.04),(sign*2.28,.38),(sign*1.7,.23)]
        m.slab(label+' blunt winglet',wing,-.23,-.10,'orange','ivory',.025)
        m.panel(label+' engine hatch',cx,.25,.785,.31,.43,'orange')
        m.panel(label+' engine lamp',cx,.18,.823,.13,.10,'amber')
        for y in [-.65,.75]:
            # Ivory fastener pads sit on the cowl instead of forming fake weapons.
            m.panel(label+' ivory service tab',cx,y,.785,.29,.11,'ivory')
    m.finish('amber-firefly','Amber Firefly',target=(0,0,.2),span=6.8)
def warden():
    m.begin('Warden')
    octagon=[(-.87,-1.15),(.87,-1.15),(1.37,-.66),(1.37,.66),(.87,1.15),(-.87,1.15),(-1.37,.66),(-1.37,-.66)]
    stack('Octagonal anchored pedestal',octagon,[(.12,.90,.90),(.24,1,1),(.51,1,1),(.65,.90,.90)],'olive','metal')
    disc('Turret rotation bearing',(0,0,.7),1.05,.18,'black','Z',24)
    disc('Bearing armored crown',(0,0,.79),1.11,.13,'olive','Z',16)
    shell=[(-.74,-.98),(.74,-.98),(1.16,-.57),(1.16,.56),(.73,1.02),(-.73,1.02),(-1.16,.56),(-1.16,-.57)]
    stack('Faceted barrel-free armored shell',shell,[(.84,.87,.89),(1.08,1,1),(1.82,1,1),(2.11,.83,.83)],'olive','olive')
    # Top cover and cheek plates carry seams without adding weapon sockets.
    cover=[(-.31,-.55),(.31,-.55),(.46,-.34),(.46,.3),(.27,.5),(-.27,.5),(-.46,.3),(-.46,-.34)]
    m.slab('Central dorsal access cover',cover,2.115,2.16,'olive','metal',.018)
    for sign in [-1,1]:
        x=sign*.72
        m.slab('Sloped upper cheek',[(x-sign*.20,-.57),(x+sign*.18,-.35),(x+sign*.18,.43),(x-sign*.17,.62)],1.99,2.065,'olive','metal',.018)
        # Vertical flank service panel, six-sided and solid.
        yz=[(-.49,1.22),(-.30,1.12),(.43,1.12),(.64,1.28),(.5,1.64),(-.3,1.67)]
        v=[(sign*(1.17+d),y,z) for d in [0,.055] for y,z in yz];n=len(yz)
        m.mesh('Solid flank armor plate',v,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],['olive','metal'],[0,0]+[1]*n,.018)
        for y in [-.32,.43]:
            ob=disc('Flank fastener',(0,0,0),.055,.025,'steel','Z',8)
            ob.rotation_euler.y=math.pi/2;ob.location=(sign*1.24,y,1.4)
        # Two compact ivory equipment boxes mounted behind the main shell.
        for z in [1.15,1.57]:
            m.slab('Rear ivory equipment module',[(sign*.78,-.85),(sign*1.06,-.85),(sign*1.06,-1.20),(sign*.78,-1.20)],z,z+.31,'ivory','ivory',.025)
    # Single nearly flush red energy core; no protruding tubes anywhere.
    for i,(y,r,mat) in enumerate([(1.034,.45,'metal'),(1.060,.385,'steel'),(1.083,.332,'black'),(1.108,.267,'red')]):
        disc('Central energy core '+str(i),(0,y,1.48),r,.028,mat,count=8)
    disc('Energy core hot center',(0,1.131,1.48),.125,.02,'amber',count=8)
    m.anchor('ShotOrigin',(0,1.145,1.48))
    # Rear radiator, seen from the sides and above.
    m.slab('Rear radiator block',[(-.69,-.95),(.69,-.95),(.69,-1.26),(-.69,-1.26)],1.10,1.91,'black','black',.025)
    for i in range(12):
        x=-.62+i*.112
        m.beam('Radiator fin',(x,-1.29,1.15),(x,-1.29,1.88),.025,'metal',4)
    for sx in [-1,1]:
        for sy in [-1,1]:
            m.beam('Splayed stabilizer link',(sx*1.04,sy*.82,.37),(sx*1.5,sy*1.18,.20),.16,'metal',8)
            m.beam('Stabilizer piston',(sx*1.0,sy*.84,.47),(sx*1.43,sy*1.16,.30),.045,'steel',8)
            outline=[(sx*1.28,sy*1.06),(sx*1.57,sy*1.02),(sx*1.85,sy*1.42),(sx*1.57,sy*1.60),(sx*1.30,sy*1.35)]
            m.slab('Grounded stabilizer foot',outline,0,.19,'olive','metal',.035)
            disc('Foot hinge',(sx*1.46,sy*1.20,.225),.12,.06,'steel','Z',12)
            m.panel('Foot hazard stripe',sx*1.62,sy*1.39,.205,.18,.17,'hazard')
    m.finish('iron-warden','Iron Warden',target=(0,0,1.05),span=5.7)
if __name__=='__main__':
    firefly();warden()

