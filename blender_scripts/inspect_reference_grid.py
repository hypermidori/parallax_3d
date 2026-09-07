"""Coordinate grid for manual measurements, not new artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R=Path(__file__).resolve().parents[1]
out=R/'output/contour-fit';out.mkdir(exist_ok=True)
im=Image.open(R/'references/player/turnaround-v01.png').convert('RGB')
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
for name,box in [('front',(285,88,425,221)),('side',(812,88,959,221)),('back',(1354,88,1500,221))]:
    x0,y0,x1,y1=box;s=6
    crop=im.crop(box).resize(((x1-x0)*s,(y1-y0)*s))
    d=ImageDraw.Draw(crop,'RGBA')
    for x in range((x0//10+1)*10,x1,10):
        u=(x-x0)*s;d.line((u,0,u,crop.height),fill=(0,140,200,75));d.text((u+1,0),str(x),font=font,fill=(0,40,60,255))
    for y in range((y0//10+1)*10,y1,10):
        v=(y-y0)*s;d.line((0,v,crop.width,v),fill=(0,140,200,75));d.text((0,v+1),str(y),font=font,fill=(0,40,60,255))
    crop.save(out/f'measure-{name}.png')
