"""Combine the existing app screenshot with the matching/evidence breakdown."""
from pathlib import Path
BASE=Path(__file__).resolve().parent
source=(BASE/'build_poster.py').read_text()
start=source.index("heading('01','From scattered issues")
end=source.index('# Right column editorial sections',start)
visual=r'''
heading('01','Discover a task. Understand the fit.',X,6.32,W)
# Fresh screenshot of the rendered app, real bundled issues and an isolated showcase profile.
shot=ROOT/'showcase-poster/Site_Discovery_Fresh.png'
from PIL import Image
with Image.open(shot) as im:
 ratio=im.height/im.width
sw=min(17.7,22.7/ratio);sh=sw*ratio
picture(shot.read_bytes(),X,7.76,sw,sh)
text('Fresh app capture · public GitHub data + showcase profile',X,7.76+sh+.27,sw,22,MUTED)
# Retain the evidence-aware matching breakdown beside the screenshot.
EX=20.15;EW=10.45
text('HOW THE MATCH IS BUILT',EX,7.89,EW,25,TEAL,True)
text('A score you\ncan inspect',EX,8.62,EW,46,N,True)
text('The match uses four profile and task factors.',EX,10.39,EW,30,MUTED)
weights=[('Technical skills',60,TEAL),('Difficulty / experience',20,N),('Civic interests',15,'527A9C'),('Availability / effort',5,GOLD)]
for i,(label,value,color) in enumerate(weights):
 y=12.07+i*1.64
 text(label,EX,y,EW-1.7,27,INK)
 text(f'{value}%',EX+EW-1.65,y,1.65,29,color,True,align='right')
 rect(EX,y+.67,EW,.29,PALE)
 rect(EX,y+.67,EW*value/100,.29,color)
text('EVIDENCE SOURCE BREAKDOWN',EX,19.22,EW,24,TEAL,True)
for i,(title,body) in enumerate([
 ('Stated or reviewed','Issue-supported requirements and curator-reviewed corrections.'),
 ('AI-inferred','Clearly labeled suggestions; counted at half weight.'),
 ('Unknown','Missing evidence stays unknown. Coverage is shown separately from fit.')]):
 y=20.08+i*2.87
 rect(EX,y,EW,2.5,PALE,LINE,.12)
 text(title,EX+.3,y+.3,EW-.6,33,N,True)
 text(body,EX+.3,y+1.02,EW-.6,27,INK)
text('Skills + civic interests → a clearer next contribution',EX,29.42,EW,34,TEAL,True)
'''
code=source[:start]+visual+'\n'+source[end:]
code=code.replace("Source bar lengths encode total issues; teal segments encode open issues.","Issue-state chart removed. Discovery screenshot is an fresh Chromium capture of the running app with real bundled GitHub data and a separate showcase contributor profile; see showcase-poster/CAPTURE_RECORD.json. Matching weights describe the implemented scoring model; they do not claim measured success rates.")
exec(compile(code,str(BASE/'build_poster.py'),'exec'),{'__file__':str(BASE/'build_poster.py'),'__name__':'__main__'})
