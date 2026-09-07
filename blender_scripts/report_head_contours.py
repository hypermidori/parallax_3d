"""Analytical overlays and independent raster checks of Blender output."""
from pathlib import Path
import json,math,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/contour-fit-smooth'
D=json.loads((OUT/'measurements.json').read_text(encoding='utf-8'));T=D['targets']
REF=Image.open(ROOT/'references/player/turnaround-v01.png').convert('RGB')
FONT='C:/Windows/Fonts/YuGothM.ttc'
def font(size):return ImageFont.truetype(FONT,size)
ORANGE='#cb4d1c';GREEN='#008c62';BLUE='#1473c8';INK='#243648'

def mask_extreme(stage,view,levels,axis,which):
    a=np.asarray(Image.open(OUT/f'{stage}-{view}.png'))[:,:,3]/255
    values=[];origin={'front':283.5,'side':820.,'back':1355.}[view]
    for level in levels:
        index=round((level-(80 if axis==0 else origin))*6-.5)
        line=a[index,:] if axis==0 else a[:,index]
        ids=np.flatnonzero(line>=.5)
        if not len(ids):values.append(float('nan'));continue
        v=(ids.min() if which=='min' else ids.max())+.5
        values.append(v/6+(origin if axis==0 else 80))
    return np.array(values)

checks={}
for stage in ('before','after'):
    L=mask_extreme(stage,'front',T['front_rows'],0,'min')
    R=mask_extreme(stage,'front',T['front_rows'],0,'max')
    side=np.array(T['side']);SS=mask_extreme(stage,'side',side[:,1],0,'min')
    crown=np.array(T['crown_front']);CC=mask_extreme(stage,'front',crown[:,0],1,'min')
    rear=np.array(T['crown_side']);RR=mask_extreme(stage,'side',rear[:,1],0,'max')
    back=np.array(T['crown_back']);BB=mask_extreme(stage,'back',back[:,0],1,'min')
    errors={'front_jaw':np.r_[L-T['front_left'],R-T['front_right']],
            'side_profile':SS-side[:,0],'crown_front':CC-crown[:,1],
            'crown_side':RR-rear[:,0],'crown_back_holdout':BB-back[:,1]}
    errors['face_combined']=np.r_[errors['front_jaw'],errors['side_profile']]
    checks[stage]={k:{'mean_abs_px':float(np.nanmean(abs(v))),'max_abs_px':float(np.nanmax(abs(v))),
                       'samples':len(v),'missing':int(np.isnan(v).sum())} for k,v in errors.items()}

(OUT/'render-verification.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
assert all(v['missing']==0 for stage in checks.values() for v in stage.values()), 'Missing rendered contour samples'
assert checks['after']['face_combined']['mean_abs_px']<checks['before']['face_combined']['mean_abs_px'], 'No improvement'

def points(c,view):
    rows=np.array(c['rows']);curves=[]
    if view=='front':
        for k in ('front_left','front_right'):
            sel=(rows>=190)&(rows<=208);curves.append(np.c_[np.array(c[k])[sel],rows[sel]])
        curves.append(np.c_[c['crown_x'],c['crown_y']])
    elif view=='side':
        sel=(rows>=175)&(rows<=209);curves.append(np.c_[np.array(c['side'])[sel],rows[sel]])
        sel=(rows>=100)&(rows<=159);curves.append(np.c_[np.array(c['rear'])[sel],rows[sel]])
    else:curves.append(np.c_[c['back_x'],c['back_y']])
    return curves

def target_points(view):
    if view=='front':return np.r_[np.c_[T['front_left'],T['front_rows']],np.c_[T['front_right'],T['front_rows']],T['crown_front']]
    if view=='side':return np.r_[T['side'],T['crown_side']]
    return np.array(T['crown_back'])

def panel(view,scale=5):
    x0={'front':283.5,'side':820.,'back':1355.}[view];dy={'front':0,'side':1,'back':2}[view]
    # Same camera window as the model render. Only registration translations.
    img=REF.transform((140*scale,150*scale),Image.Transform.EXTENT,(x0,80+dy,x0+140,230+dy),Image.Resampling.BICUBIC)
    img=Image.blend(img,Image.new('RGB',img.size,'white'),.15)
    draw=ImageDraw.Draw(img)
    def px(p):return ((p[0]-x0)*scale,(p[1]-80)*scale)
    for stage,color in [('before',ORANGE),('after',GREEN)]:
        for curve in points(D['contours'][stage],view):
            run=[]
            for i,p in enumerate(curve):
                if np.isfinite(p).all():
                    if stage=='after' or (i//5)%2==0:run.append(px(p))
                    else:
                        if len(run)>1:draw.line(run,fill=color,width=3)
                        run=[]
                else:
                    if len(run)>1:draw.line(run,fill=color,width=3)
                    run=[]
            if len(run)>1:draw.line(run,fill=color,width=3)
    for p in target_points(view):
        u,v=px(p);draw.ellipse((u-3,v-3,u+3,v+3),outline=BLUE,width=2)
    return img

W=1480;H=1030
sheet=Image.new('RGB',(W,H),'#f1f5f8');draw=ImageDraw.Draw(sheet)
draw.text((35,18),'頭部の輪郭フィット / 実際のメッシュ投影を重ねて比較',font=font(29),fill=INK)
draw.line((40,80,95,80),fill=ORANGE,width=4);draw.text((105,63),'調整前',font=font(21),fill=INK)
draw.line((245,80,300,80),fill=GREEN,width=4);draw.text((310,63),'調整後',font=font(21),fill=INK)
draw.ellipse((458,76,466,84),outline=BLUE,width=2);draw.text((480,63),'図から読み取った測定点',font=font(21),fill=INK)
draw.text((1000,63),'元画像の 1 px = 表示の 5 px',font=font(18),fill=INK)
for view,x,label in [('front',25,'正面：顎と頭頂'),('side',755,'側面：横顔と頭頂後方')]:
    draw.text((x+10,111),label,font=font(24),fill=INK);sheet.paste(panel(view),(x,155))
b=checks['before']['face_combined']['mean_abs_px'];a=checks['after']['face_combined']['mean_abs_px']
draw.text((35,923),f'顔の輪郭 37 点：平均ずれ {b:.2f} → {a:.2f} px（別途、描画画像の輪郭でも検証）',font=font(23),fill=INK)
draw.text((35,962),'輪郭の読取誤差は約 ±2 px。隠れた頭蓋・目・頬の丸み・髪型全体の再現度は、この値では評価していません。',font=font(19),fill=INK)
draw.text((35,995),'調整前・後はいずれも今回作った断面式の検証用メッシュです。以前の顔モデルの完成度比較ではありません。',font=font(17),fill=INK)
sheet.save(OUT/'overlay-comparison.png')

back=Image.new('RGB',(760,895),'#f1f5f8');bd=ImageDraw.Draw(back)
bd.text((30,15),'背面の頭頂 / 調整に使わない確認用',font=font(25),fill=INK)
back.paste(panel('back'),(30,65))
bh=checks['after']['crown_back_holdout']['mean_abs_px']
bd.text((30,835),f'調整後の平均ずれ {bh:.2f} px。背面の測定点とは差が残る。',font=font(20),fill=INK)
back.save(OUT/'back-check.png')

geo=Image.new('RGB',(1530,740),'#e7edf1');gd=ImageDraw.Draw(geo)
gd.text((25,15),'調整後の立体 / 顔の絵を貼らない、輪郭だけの検証用形状',font=font(27),fill=INK)
for i,(view,label) in enumerate([('front','正面'),('side','側面'),('three-quarter','斜め')]):
    render=Image.open(OUT/f'after-{view}.png').convert('RGBA');render.thumbnail((490,565))
    gd.text((i*510+25,67),label,font=font(22),fill=INK)
    geo.paste(render,(i*510+10,112),render)
gd.text((25,678),'頭頂の紫色は髪の外形を測る仮の面です。目・口の造形、前髪、耳、首はまだ作っていません。',font=font(21),fill=INK)
geo.save(OUT/'geometry-review.png')
for fn in ('ATTRIBUTION.md','OGA-BY-3.0.txt'):shutil.copy2(ROOT/'references/base-mesh'/fn,OUT/fn)
with (OUT/'ATTRIBUTION.md').open('a',encoding='utf-8') as credit:
    credit.write('\n## Current contour experiment\n\nThe smooth contour experiment constructs new cross-section envelopes. It does not retain the original facial topology or texture. The earlier head study supplies the scene and approximate initial proportions. The source credit and license are preserved to document that lineage.\n')
print(json.dumps(checks,indent=2))
