import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'output/contour-fit-smooth'
result={'meshes':[]}
for ob in bpy.context.scene.objects:
    if ob.type!='MESH':continue
    me=ob.data
    finite=all(math.isfinite(c) for v in me.vertices for c in v.co)
    repaired=me.validate(verbose=True,clean_customdata=False)
    assert finite and not repaired,ob.name
    me.calc_loop_triangles()
    result['meshes'].append({'name':ob.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),
                            'finite':finite,'validation_needed_repairs':repaired,
                            'shape_keys':list(me.shape_keys.key_blocks.keys())})
ref=[im for im in bpy.data.images if im.name.startswith('turnaround-v01') and im.users>0]
assert ref and ref[-1].packed_file
result['reference_image_packed']=True
for block in list(bpy.data.texts):bpy.data.texts.remove(block)
result['embedded_scripts_removed']=True
bpy.ops.wm.save_as_mainfile(filepath=str(O/'head-contour-fit.blend'))
(O/'file-check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
