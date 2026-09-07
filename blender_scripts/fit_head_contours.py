"""Fit actual subdivided mesh projections to explicit reference measurements.

No target image is used as model texture. Front/back crown disagreement is
reported independently; occluded skull surfaces are deliberately unscored.
"""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/contour-fit';OUT.mkdir(exist_ok=True)
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

# Only a head is compared: remove the previous neck stump, close the underside.
bm=bmesh.new();bm.from_mesh(head.data)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<.0001 and v.co.y>-.075],context='VERTS')
bound=[e for e in bm.edges if e.is_boundary]
if bound:bmesh.ops.holes_fill(bm,edges=bound,sides=0)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(head.data);bm.free()

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
for it in range(24):
    m=measure();hv=npverts(head);cv=npverts(cap)
    py=CHIN-hv[:,2]/S
    # Smooth per-height affine correction of the front silhouette. Translation
    # allows the small asymmetry in the drawing, rather than hiding it by mirror.
    widths=(m['front_right']-m['front_left'])
    ratio=np.clip((front_right-front_left)/widths,.65,1.5)
    mid_old=(m['front_left']+m['front_right'])/2-FX
    mid_new=(front_left+front_right)/2-FX
    rows=np.r_[175,front_rows,212,225]
    rat=np.interp(py,rows,np.r_[1,ratio,ratio[-1],1])
    mo=np.interp(py,rows,np.r_[0,mid_old,mid_old[-1],0])*S
    mn=np.interp(py,rows,np.r_[0,mid_new,mid_new[-1],0])*S
    hv[:,0]+=.65*((hv[:,0]-mo)*rat+mn-hv[:,0])
    # Profile displacement fades to zero in the back half of the head.
    delta=(side_x-m['side'])*S
    corr=np.interp(py,np.r_[160,side_rows,213,230],np.r_[0,delta,delta[-1],0])
    frontness=np.clip((.025-hv[:,1])/.095,0,1)
    hv[:,1]+=.65*corr*frontness
    # Move crown vertices vertically by measured top-boundary residual.
    cx=FX+cv[:,0]/S;topdelta=(m['crown']-front_crown[:,1])*S
    dc=np.interp(cx,front_crown[:,0],topdelta)
    height_weight=np.clip((cv[:,2]-.13)/.055,0,1)
    cv[:,2]+=.55*dc*height_weight
    # Rear depth correction is measured in the side view, independent of front.
    cy=CHIN-cv[:,2]/S
    dr=np.interp(cy,side_back[:,1],(side_back[:,0]-m['crown_side'])*S)
    rear_weight=np.clip((cv[:,1]-.025)/.045,0,1)
    cv[:,1]+=.55*dr*rear_weight
    setverts(head,hv);setverts(cap,cv)
    h={'iteration':it+1,'metrics':metrics(measure())};history.append(h)
    print('FIT',it+1,json.dumps(h['metrics']['visible_face_combined']),flush=True)

after=measure();after_v=npverts(head);after_cap=npverts(cap)

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
head['scope']='Facial silhouette fit only; no eyes, texture, rig or finished hair'
head['source']='Chloe Wolfe; OGA-BY 3.0; see ATTRIBUTION.md'
head['measured_reference_pixel_scale_m']=S
cap['scope']='Crown envelope only; not a hairstyle or inferred skull'
for ob,old in [(head,before_v),(cap,before_cap)]:
    ob.shape_key_add(name='Fitted basis');key=ob.shape_key_add(name='Before contour fitting')
    for p,c in zip(key.data,old):p.co=c
    key.value=0
camera.location=(.9,-2,.36);aim(camera,(0,0,.105))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'head-contour-fit.blend'))

data={'registration':{'scale_m_per_pixel':S,'front_center_x':FX,'side_origin_x':SY,'back_center_x':BX,'chin_y':CHIN,
 'side_up_px':1,'back_up_px':2,'note':'Translations only, no independent nonuniform image scaling.'},
 'targets':{'front_rows':front_rows.tolist(),'front_left':front_left.tolist(),'front_right':front_right.tolist(),
 'side':np.c_[side_x,side_rows].tolist(),'crown_front':front_crown.tolist(),'crown_back':back_crown.tolist(),'crown_side':side_back.tolist()},
 'uncertainty_px':2,'metrics':{'before':metrics(before),'after':metrics(after)},'history':history,'contours':all_dense,
 'notes':['Measurements are manual traces, not ground-truth geometry.','Only visible jaw/profile and exposed crown are scored.',
 'Back crown is an independent check, not optimized. Front and back silhouettes need not agree in the generated drawing.',
 'Dense evaluation uses actual subdivided mesh edges. Rendered masks are checked separately.',
 'This is a fitting experiment, not a finished character.']}
(OUT/'measurements.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print('FINAL_METRICS',json.dumps(data['metrics']),flush=True)
