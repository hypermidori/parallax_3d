"""Fit actual subdivided mesh projections to explicit reference measurements.

No target image is used as model texture. Front/back crown disagreement is
reported independently; occluded skull surfaces are deliberately unscored.
"""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/contour-fit-smooth';OUT.mkdir(exist_ok=True)
S=.002;FX=353.5;SY=890.;BX=1425.;CHIN=210.
scene=bpy.context.scene
head=bpy.data.objects['Fitted_Base_Head'];cap=bpy.data.objects['Scalp']
for ob in list(bpy.data.objects):
    if ob not in (head,cap):bpy.data.objects.remove(ob,do_unlink=True)
for ob in (head,cap):
    ob.hide_set(False);ob.hide_render=False
    ob.data.materials.clear()
    for p in ob.data.polygons:p.material_index=0;p.use_smooth=True
    bpy.context.view_layer.objects.active=ob
    # Add editable degrees of freedom once. Further subdivision stays fixed
    # before and after optimization, so both measurements use the same mesh.
    ob.modifiers[0].levels=1
    bpy.ops.object.modifier_apply(modifier=ob.modifiers[0].name)
    sub=ob.modifiers.new('Fixed evaluation subdivision','SUBSURF');sub.levels=1;sub.render_levels=1

def pchip(x,y,q):
    """Shape-preserving cubic interpolation, with no external dependency."""
    x=np.asarray(x,float);y=np.asarray(y,float);q=np.asarray(q,float)
    h=np.diff(x);d=np.diff(y)/h;sl=np.zeros_like(y);sl[0]=d[0];sl[-1]=d[-1]
    for i in range(1,len(x)-1):
        if d[i-1]*d[i]>0:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1];sl[i]=(w1+w2)/(w1/d[i-1]+w2/d[i])
    q=np.clip(q,x[0],x[-1]);i=np.clip(np.searchsorted(x,q)-1,0,len(x)-2)
    t=(q-x[i])/h[i]
    return (2*t**3-3*t*t+1)*y[i]+(t**3-2*t*t+t)*h[i]*sl[i]+(-2*t**3+3*t*t)*y[i+1]+(t**3-t*t)*h[i]*sl[i+1]

# Rebuild a smooth cross-section cage instead of distorting the detailed face.
# This stage intentionally has no eyes or lips: only the head envelope is tested.
# Initial dimensions approximate the previous base, not the target contour.
pr=np.array([96,100,110,120,130,140,150,160,170,180,190,194,198,202,206,208,210],float)
pw=np.array([.01,20,35,42,45,46,46,44,40,34,31.5,28.5,25,21,14,9,.01])
pf=np.array([890,870,850,839,832,831,832,834,838,837,834,835,837,839,842,844,847])
pb=np.array([890,910,928,940,946,949,949,948,945,936,923,914,902,885,867,859,847])
angles=np.arange(64)*2*math.pi/64
def envelope(ob,crown=False):
    vs=[];fs=[];rows=115 if not crown else 80;cols=len(angles)
    for ri in range(rows):
        if crown:
            py=94+(151-19*np.cos(angles)-94)*ri/(rows-1)
            w=pchip([94,98,105,115,125,140,170],[.01,21,36,46,50,51,46],py)
            f=pchip([94,100,110,125,140,160,180],[890,872,855,839,830,833,842],py)
            b=pchip([94,100,110,125,140,160,180],[890,914,933,944,950,950,938],py)
        else:
            py=np.full(cols,96+(210-96)*ri/(rows-1));w=pchip(pr,pw,py);f=pchip(pr,pf,py);b=pchip(pr,pb,py)
        xx=np.sin(angles)*w
        co=np.cos(angles);yy=(f+b)/2-(b-f)/2*np.sign(co)*abs(co)**.5
        if not crown:
            # Preserve a small localized nose ridge instead of spreading the
            # profile displacement across the whole width of the face.
            bump=2.0*np.exp(-((py-183)/4)**2)
            yy+=bump*(1-np.exp(-(xx/7)**2))*np.clip(co,0,1)
        vs.extend(zip(xx*S,(yy-SY)*S,(CHIN-py)*S))
    for r in range(rows-1):
        for j in range(cols):fs.append((r*cols+j,r*cols+(j+1)%cols,(r+1)*cols+(j+1)%cols,(r+1)*cols+j))
    fs.append(tuple(reversed(range(cols))))
    if not crown:fs.append(tuple((rows-1)*cols+j for j in range(cols)))
    me=bpy.data.meshes.new('Measured cross-section envelope');me.from_pydata(vs,[],fs);me.update()
    ob.data=me;ob.modifiers.clear()
    for p in me.polygons:p.use_smooth=True
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
envelope(head);envelope(cap,True)
head.name='Head envelope - no facial details';cap.name='Measured crown envelope'

def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=.85;bs.inputs['Specular IOR Level'].default_value=.15
    return m
head.data.materials.append(material('Untextured head',(.42,.51,.55)))
cap.data.materials.append(material('Crown envelope / not finished hair',(.32,.23,.47)))

# Manually read points on the ink boundary. Coordinates are ORIGINAL pixels.
# Side reference is translated upward 1 px (chin 211 -> 210). Back is up 2 px.
# Hair crossing the cheek at y<190 is not a facial silhouette measurement.
front_rows=np.array([190,192,194,196,198,200,202,204,206,208],float)
front_left=np.array([327,328,329,330.5,332.5,335,338,341,345,349],float)
front_right=np.array([381,380,378.5,376.5,374.5,372,369,366,362,357],float)
side_raw=np.array([[841,176],[839,178],[837,180],[834,182],[832,183.5],
 [833,186],[834.5,189],[836,191],[836,193],[838,195],[838.5,197],
 [840,199],[841.5,201],[842.5,203],[843,205],[843.5,207],[845,210]],float)
side_rows=side_raw[:,1]-1;side_x=side_raw[:,0]
# Traced crown is sampled vertically, so the very top is measured as well.
front_crown=np.array([[313,111],[320,106],[327,102],[334,99],[341,97.2],
 [348,96],[355,96.2],[362,96.3],[369,97.3],[376,99.5],[383,103],
 [390,107.5],[395,112]],float)
back_crown=np.array([[1388,112],[1395,108],[1402,104],[1409,101.3],[1416,99.7],
 [1423,99],[1430,99.2],[1437,100.1],[1444,102.4],[1451,105.8],[1458,110.3]],float)
back_crown[:,1]-=2
# Side crown rear boundary is exposed; fin and ear cup are excluded.
side_back=np.array([[903,101],[912,105],[920,111],[927,119],[932,129],
 [935,140],[936.5,150],[937.5,160]],float);side_back[:,1]-=1

def evaluated(ob):
    bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    v=np.array([v.co[:] for v in me.vertices]);e=np.array([e.vertices[:] for e in me.edges])
    ev.to_mesh_clear();return v,e

def crossings(v,e,axis,levels,out_axis,which='min'):
    a=v[e[:,0]];b=v[e[:,1]];res=[]
    for level in levels:
        den=b[:,axis]-a[:,axis]
        ok=(np.minimum(a[:,axis],b[:,axis])<=level)&(np.maximum(a[:,axis],b[:,axis])>=level)&(abs(den)>1e-10)
        if not ok.any():res.append(float('nan'));continue
        t=(level-a[ok,axis])/den[ok];p=a[ok,out_axis]+t*(b[ok,out_axis]-a[ok,out_axis])
        res.append(float(p.min() if which=='min' else p.max()))
    return np.array(res)

def measure():
    v,e=evaluated(head);cv,ce=evaluated(cap)
    z=(CHIN-front_rows)*S
    left=crossings(v,e,2,z,0,'min')/S+FX;right=crossings(v,e,2,z,0,'max')/S+FX
    side=crossings(v,e,2,(CHIN-side_rows)*S,1,'min')/S+SY
    top=CHIN-crossings(cv,ce,0,(front_crown[:,0]-FX)*S,2,'max')/S
    rear=crossings(cv,ce,2,(CHIN-side_back[:,1])*S,1,'max')/S+SY
    back=CHIN-crossings(cv,ce,0,-(back_crown[:,0]-BX)*S,2,'max')/S
    return dict(front_left=left,front_right=right,side=side,crown=top,crown_side=rear,crown_back=back)

targets=dict(front_left=front_left,front_right=front_right,side=side_x,crown=front_crown[:,1],crown_side=side_back[:,0],crown_back=back_crown[:,1])
def metrics(m):
    r={}
    for k,t in targets.items():
        d=m[k]-t;r[k]={'mean_abs_px':float(np.nanmean(abs(d))),'max_abs_px':float(np.nanmax(abs(d))),'samples':len(t),'missing':int(np.isnan(d).sum())}
    face=np.r_[m['front_left']-front_left,m['front_right']-front_right,m['side']-side_x]
    r['visible_face_combined']={'mean_abs_px':float(np.nanmean(abs(face))),'max_abs_px':float(np.nanmax(abs(face))),'samples':len(face)}
    return r

def npverts(ob):return np.array([v.co[:] for v in ob.data.vertices])
def setverts(ob,v):
    ob.data.vertices.foreach_set('co',np.asarray(v,dtype=np.float32).ravel());ob.data.update()

before=measure();before_v=npverts(head);before_cap=npverts(cap)
history=[{'iteration':0,'metrics':metrics(before)}]
for it in range(12):
    m=measure();hv=npverts(head);cv=npverts(cap)
    py=CHIN-hv[:,2]/S
    # Smooth per-height affine correction of the front silhouette. Translation
    # allows the small asymmetry in the drawing, rather than hiding it by mirror.
    widths=(m['front_right']-m['front_left'])
    ratio=np.clip((front_right-front_left)/widths,.65,1.5)
    mid_old=(m['front_left']+m['front_right'])/2-FX
    mid_new=(front_left+front_right)/2-FX
    rows=np.r_[175,front_rows,212,225]
    rat=pchip(rows,np.r_[1,ratio,ratio[-1],1],py)
    mo=pchip(rows,np.r_[0,mid_old,mid_old[-1],0],py)*S
    mn=pchip(rows,np.r_[0,mid_new,mid_new[-1],0],py)*S
    hv[:,0]+=.65*((hv[:,0]-mo)*rat+mn-hv[:,0])
    # Profile displacement fades to zero in the back half of the head.
    delta=(side_x-m['side'])*S
    corr=pchip(np.r_[160,side_rows,213,230],np.r_[0,delta,delta[-1],0],py)
    frontness=np.clip((.025-hv[:,1])/.095,0,1)
    hv[:,1]+=.65*corr*frontness
    # Move crown vertices vertically by measured top-boundary residual.
    cx=FX+cv[:,0]/S;topdelta=(m['crown']-front_crown[:,1])*S
    dc=pchip(front_crown[:,0],topdelta,cx)
    height_weight=np.clip((cv[:,2]-.13)/.055,0,1)
    cv[:,2]+=.55*dc*height_weight
    # Rear depth correction is measured in the side view, independent of front.
    cy=CHIN-cv[:,2]/S
    dr=pchip(side_back[:,1],(side_back[:,0]-m['crown_side'])*S,cy)
    rear_weight=np.clip((cv[:,1]-.025)/.045,0,1)
    cv[:,1]+=.55*dr*rear_weight
    setverts(head,hv);setverts(cap,cv)
    h={'iteration':it+1,'metrics':metrics(measure())};history.append(h)
    print('FIT',it+1,json.dumps(h['metrics']['visible_face_combined']),flush=True)

after=measure();after_v=npverts(head);after_cap=npverts(cap)
# The unseen upper skull must stay inside the hair envelope. A smooth 5 px
# inset avoids the old skull protruding through the newly measured crown.
hv=after_v.copy();py=CHIN-hv[:,2]/S
weight=np.clip((175-py)/45,0,1)
hv[:,2]-=weight*.009
hv[:,1]+=(.005-hv[:,1])*weight*.10
hv[:,0]*=1-weight*.05
# Confine the nose/lip profile to the middle of the face. Extending a side
# profile across every latitude would create horizontal ridges on the cheeks.
for start in range(0,len(hv),64):
    ring=hv[start:start+64];row=CHIN-ring[0,2]/S
    if row<158:continue
    current_front=ring[:,1].min()/S+SY
    cheek=float(pchip([158,170,180,190,200,210],[837,839,840,840,842,847],row))
    center=(ring[:,0].min()+ring[:,0].max())/2
    off=(ring[:,0]-center)/S
    factor=(1-np.exp(-(off/6.0)**2))*np.clip(np.cos(angles),0,1)**2
    ring[:,1]+=(cheek-current_front)*S*factor
    ring[:,1]=np.maximum(ring[:,1],(current_front-SY)*S)
# Keep the posterior skull inside the measured hair envelope as well.
py=CHIN-hv[:,2]/S
limit=(pchip(side_back[:,1],side_back[:,0],py)-SY-3)*S
blend=np.clip((176-py)/16,0,1)
for start in range(0,len(hv),64):
    ring=hv[start:start+64];ymax=ring[:,1].max()
    if ymax>0:
        row=CHIN-ring[0,2]/S
        anatomical=(float(pchip([96,110,130,150,160,170,180,190,200,210],
                    [890,915,927,930,930,925,918,907,880,847],row))-SY)*S
        permitted=min(ymax,limit[start] if row<160 else anatomical)
        ratio=max(.05,permitted/ymax)
        ring[:,1]*=1-(1-ratio)*np.clip(ring[:,1]/.02,0,1)
# Smooth the unconstrained interior surface. Keep the measured front profile
# (theta=0) and every ring's x-extents unchanged. No image-space correction.
ygrid=hv[:,1].reshape(-1,64);lo=ygrid.min(axis=1);hi=ygrid.max(axis=1)
kernel=np.exp(-.5*(np.arange(-8,9)/3.)**2);kernel/=kernel.sum()
padded=np.pad(ygrid,((8,8),(0,0)),mode='edge')
smooth=sum(w*padded[i:i+len(ygrid)] for i,w in enumerate(kernel))
smooth=(np.roll(smooth,1,axis=1)+2*smooth+np.roll(smooth,-1,axis=1))/4
distance=np.minimum(np.arange(64),64-np.arange(64))
mix=1-np.exp(-(distance/1.7)**2)
rowmix=np.minimum(1,np.arange(len(ygrid))[::-1]/3.)
ygrid+=rowmix[:,None]*mix[None,:]*(smooth-ygrid)
ygrid[:]=np.clip(ygrid,lo[:,None],hi[:,None])
setverts(head,hv);after_v=hv;after=measure()

# Output dense evaluated contours; the report plots these, not the target itself.
def dense():
    v,e=evaluated(head);cv,ce=evaluated(cap)
    rows=np.arange(100,211,.25);z=(CHIN-rows)*S
    crown_x=np.arange(307,401,.25);back_x=np.arange(1379,1472,.25)
    return dict(rows=rows.tolist(),front_left=(crossings(v,e,2,z,0)/S+FX).tolist(),
        front_right=(crossings(v,e,2,z,0,'max')/S+FX).tolist(),
        side=(crossings(v,e,2,z,1)/S+SY).tolist(),
        crown_x=crown_x.tolist(),crown_y=(CHIN-crossings(cv,ce,0,(crown_x-FX)*S,2,'max')/S).tolist(),
        rear=(crossings(cv,ce,2,z,1,'max')/S+SY).tolist(),
        back_x=back_x.tolist(),back_y=(CHIN-crossings(cv,ce,0,-(back_x-BX)*S,2,'max')/S).tolist())

scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.film_transparent=True;scene.render.image_settings.color_mode='RGBA'
scene.world=bpy.data.worlds.new('Contour study world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.resolution_x=840;scene.render.resolution_y=900;scene.render.resolution_percentage=100
def aim(ob,t):ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power in [('Key',(-.8,-1.5,1.6),65),('Fill',(1,-.4,.7),25)]:
    bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.name=name;ob.data.energy=power;ob.data.size=1.5;aim(ob,(0,0,.12))
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=.300;scene.camera=camera
# 140 x 150 reference pixels. One reference pixel becomes 6 rendered pixels.
views={'front':((0,-3,.110),(0,0,.110)),'side':((3,0,.110),(0,0,.110)),
       'back':((0,3,.110),(0,0,.110)),'three-quarter':((.9,-2,.36),(0,0,.105))}
all_dense={}
for stage,hv,cv in [('before',before_v,before_cap),('after',after_v,after_cap)]:
    setverts(head,hv);setverts(cap,cv);all_dense[stage]=dense()
    for view,(loc,targ) in views.items():
        camera.location=loc;aim(camera,targ)
        scene.render.filepath=str(OUT/f'{stage}-{view}.png');bpy.ops.render.render(write_still=True)

# Add actual registered image planes, visible from orthographic modeling views.
ref=bpy.data.images.load(str(ROOT/'references/player/turnaround-v01.png'));ref.pack()
collection=bpy.data.collections.new('Measured reference planes');scene.collection.children.link(collection)
for name,loc,rot,anchor,dy in [('Front',(0,.35,0),(math.pi/2,0,0),FX,0),('Side',(-.35,0,0),(math.pi/2,0,math.pi/2),SY,1),('Back',(0,-.35,0),(math.pi/2,0,math.pi),BX,2)]:
    ob=bpy.data.objects.new(name+' reference',None);ob.empty_display_type='IMAGE';ob.data=ref;ob.empty_display_size=1774*S
    ob.empty_image_offset=(-anchor/1774,-(887-CHIN-dy)/887);ob.location=loc;ob.rotation_euler=rot
    ob.color[3]=.3;ob.empty_image_depth='BACK';ob.hide_render=True;collection.objects.link(ob)

for ob in scene.objects:ob.select_set(False)
head.select_set(True);bpy.context.view_layer.objects.active=head
head['scope']='Smooth head-envelope fitting only; no detailed face, eyes, texture, rig or finished hair'
head['source']='Chloe Wolfe; OGA-BY 3.0; see ATTRIBUTION.md'
head['measured_reference_pixel_scale_m']=S
cap['scope']='Crown envelope only; not a hairstyle or inferred skull'
for ob,old in [(head,before_v),(cap,before_cap)]:
    ob.shape_key_add(name='Fitted basis');key=ob.shape_key_add(name='Before contour fitting')
    for p,c in zip(key.data,old):p.co=c
    key.value=0
camera.location=(.9,-2,.36);aim(camera,(0,0,.105))
for block in list(bpy.data.texts):bpy.data.texts.remove(block)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'head-contour-fit.blend'))

data={'registration':{'scale_m_per_pixel':S,'front_center_x':FX,'side_origin_x':SY,'back_center_x':BX,'chin_y':CHIN,
 'side_up_px':1,'back_up_px':2,'note':'Translations only, no independent nonuniform image scaling.'},
 'targets':{'front_rows':front_rows.tolist(),'front_left':front_left.tolist(),'front_right':front_right.tolist(),
 'side':np.c_[side_x,side_rows].tolist(),'crown_front':front_crown.tolist(),'crown_back':back_crown.tolist(),'crown_side':side_back.tolist()},
 'uncertainty_px':2,'metrics':{'before':metrics(before),'after':metrics(after)},'history':history,'contours':all_dense,
 'notes':['Measurements are manual traces, not ground-truth geometry.','Only visible jaw/profile and exposed crown are scored.',
 'A new smooth cross-section mesh is used; the previous detailed face is not preserved.',
 'Before and after are the initial and fitted cross-section meshes, not the previous finished-looking head.',
 'Back crown is an independent check, not optimized. Front and back silhouettes need not agree in the generated drawing.',
 'Dense evaluation uses actual subdivided mesh edges. Rendered masks are checked separately.',
 'This is a fitting experiment, not a finished character.']}
(OUT/'measurements.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print('FINAL_METRICS',json.dumps(data['metrics']),flush=True)
