"""Build an editable 48 x 36 inch PPTX and matching vector PDF.
Dependencies: python-pptx, reportlab, Pillow. No network or paid AI calls.
"""
from pathlib import Path
from io import BytesIO
import json, zipfile, math
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]; OUT=Path(__file__).resolve().parent
TEMPLATE=ROOT/'SENIOR SHOWCASE POSTER TEMPLATE UPDATED 8-6-2026.pptx'
N='002D62'; RED='C8102E'; TEAL='087F8C'; INK='172D43'; MUTED='4C6174'; PALE='F0F5F9'; LINE='D7E2EB'; WHITE='FFFFFF'; LIGHT='A8BBD0'; GOLD='B77A13'
prs=Presentation();prs.slide_width=Inches(48);prs.slide_height=Inches(36)
slide=prs.slides.add_slide(prs.slide_layouts[6])
pdfmetrics.registerFont(TTFont('Lato', '/usr/share/fonts/truetype/lato/Lato-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Lato-Bold', '/usr/share/fonts/truetype/lato/Lato-Bold.ttf'))
c=canvas.Canvas(str(OUT/'Civic_Issue_Matchmaker_Poster.pdf'),pagesize=(48*72,36*72))
c.setTitle('Civic Issue Matchmaker | Group 26 | Senior Design Showcase')
c.setAuthor('Davian Brooks; Michael Anstett; Tariq Khan; Andre Walia; David Landivar')
checks=[]
def rgb(color):return tuple(int(color[i:i+2],16)/255 for i in (0,2,4))
def rect(x,y,w,h,fill=WHITE,stroke=None,r=0):
 s=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if r else MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
 if r:
  try:s.adjustments[0]=.08
  except:pass
 s.fill.solid();s.fill.fore_color.rgb=RGBColor.from_string(fill)
 if stroke:s.line.color.rgb=RGBColor.from_string(stroke);s.line.width=Pt(1.2)
 else:s.line.fill.background()
 c.setFillColorRGB(*rgb(fill))
 if stroke:c.setStrokeColorRGB(*rgb(stroke))
 if r:c.roundRect(x*72,(36-y-h)*72,w*72,h*72,r*72,fill=1,stroke=bool(stroke))
 else:c.rect(x*72,(36-y-h)*72,w*72,h*72,fill=1,stroke=bool(stroke))
 return s

def text(txt,x,y,w,size=34,color=INK,bold=False,leading=1.20,align='left',h=None):
 font='Lato-Bold' if bold else 'Lato';lines=[]
 for para in txt.split('\n'):
  line=''
  for word in para.split():
   candidate=(line+' '+word).strip()
   if pdfmetrics.stringWidth(candidate,font,size)>w*72 and line:
    lines.append(line);line=word
   else:line=candidate
  lines.append(line)
 ht=len(lines)*size*leading/72+.08
 if h is not None:assert ht<=h+.06,(txt[:40],ht,h)
 assert x>=0 and y>=0 and x+w<=48.01 and y+ht<=36.01,(txt[:40],x,y,w,ht)
 for i,line in enumerate(lines):
  s=slide.shapes.add_textbox(Inches(x),Inches(y+i*size*leading/72),Inches(w),Inches(size*leading/72+.03))
  tf=s.text_frame;tf.clear();tf.word_wrap=False
  tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
  p=tf.paragraphs[0];p.text=line;p.font.name='Lato';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color)
  from pptx.enum.text import PP_ALIGN
  p.alignment={'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}[align]
  p.space_before=Pt(0);p.space_after=Pt(0)
  c.setFillColorRGB(*rgb(color));c.setFont(font,size)
  # Font ascender aligns the two rendering systems closely.
  baseline=(36-y-i*size*leading/72)*72-size*.805
  if align=='center':c.drawCentredString((x+w/2)*72,baseline,line)
  elif align=='right':c.drawRightString((x+w)*72,baseline,line)
  else:c.drawString(x*72,baseline,line)
 checks.append((txt,x,y,w,ht))
 return ht

def picture(blob,x,y,w,h):
 slide.shapes.add_picture(BytesIO(blob),Inches(x),Inches(y),width=Inches(w),height=Inches(h))
 from reportlab.lib.utils import ImageReader
 c.drawImage(ImageReader(BytesIO(blob)),x*72,(36-y-h)*72,w*72,h*72,mask='auto')

def heading(num,title,x,y,w):
 text(num,x,y,.85,28,TEAL,True)
 text(title,x+1,y-.04,w-1,42,N,True)
 rect(x,y+.82,w,.035,LINE)

def arrow(x,y,w=.5,color=TEAL):
 s=slide.shapes.add_shape(MSO_SHAPE.CHEVRON,Inches(x),Inches(y),Inches(w),Inches(.58));s.fill.solid();s.fill.fore_color.rgb=RGBColor.from_string(color);s.line.fill.background()
 c.setFillColorRGB(*rgb(color));p=c.beginPath();p.moveTo(x*72,(36-y)*72);p.lineTo((x+w*.62)*72,(36-y)*72);p.lineTo((x+w)*72,(36-y-.29)*72);p.lineTo((x+w*.62)*72,(36-y-.58)*72);p.lineTo(x*72,(36-y-.58)*72);p.lineTo((x+w*.38)*72,(36-y-.29)*72);p.close();c.drawPath(p,fill=1,stroke=0)

# Retain official FAU marks from the supplied template; all new content is editable.
with zipfile.ZipFile(TEMPLATE) as z:
 owl=z.read('ppt/media/image1.png');fau=z.read('ppt/media/image2.png')
rect(0,0,48,36,WHITE)
rect(0,0,48,5.55,N);rect(0,5.55,48,.13,RED)
picture(owl,40.24,.91,6.3,3.57)
text('Civic Issue\nMatchmaker',1.45,.66,16.2,88,WHITE,True,1.02)
text('Technical skills. Public purpose.',1.49,3.42,16.3,35,WHITE)
text('EGN 4952C  |  Electrical Engineering & Computer Science',1.49,4.4,18.1,24,WHITE)
text('TEAM MEMBERS · GROUP 26',19.1,.73,9.5,26,WHITE,True)
text('Davian Brooks\nMichael Anstett\nTariq Khan\nAndre Walia\nDavid Landivar',19.1,1.38,9.5,30,WHITE,False,1.13)
text('PROJECT ADVISOR',30.0,.73,9.0,26,WHITE,True)
text('Dr. Hari Kalva',30.0,1.38,9.0,34,WHITE,True)
text('SPONSOR',30.0,2.5,9.0,26,WHITE,True)
text('Code for America',30.0,3.15,9.0,34,WHITE,True)
text('FACULTY COURSE FACILITATORS',30.0,4.32,9.5,19,WHITE,True)
text('Dr. Hanqi Zhuang · Dr. Rabia Shahid',30.0,4.73,9.5,19,WHITE)
# Visual region and text column match the template's overall organization.
X=1.45; W=29.15; RX=32.15; RW=14.35
heading('01','From scattered issues to a clear next step',X,6.32,W)
text('Find software work that supports a civic cause—and understand why it fits.',X,7.53,W,33,MUTED)
# Architecture flow: native editable shapes.
boxes=[('PUBLIC SOURCES','GitHub issues','5 civic-tech repositories'),('TRUSTED CATALOG','Sync + enrich','Cached evidence + review'),('PERSONAL FIT','Explain + rank','Skills, interests, experience')]
for i,(tag,title,sub) in enumerate(boxes):
 x=X+i*9.95
 rect(x,8.68,9.25,3.65,PALE,LINE,.16)
 text(tag,x+.36,9.02,8.53,23,TEAL,True)
 text(title,x+.36,9.73,8.53,42,N,True)
 text(sub,x+.36,10.71,8.53,28,MUTED)
 if i<2:arrow(x+9.4,10.1,.4)
rect(X,12.69,W,1.18,N,r=.12)
text('Contributor profile → explained recommendations → contribution tracking',X+.38,12.98,W-.76,32,WHITE,True,align='center')
text('React interface  /  FastAPI services  /  SQLite storage  /  read-only GitHub API',X,14.12,W,25,MUTED,align='center')
# Source chart
heading('02','Real civic-tech issue data',X,15.33,14.15)
text('21,558',X,16.55,8,78,N,True)
text('public issues in the bundled snapshot',X,17.74,14.15,28,MUTED)
rect(X,18.51,.28,.28,TEAL);text('Open',X+.42,18.43,2.3,22,MUTED)
rect(X+2.75,18.51,.28,.28,LIGHT);text('Closed',X+3.17,18.43,2.7,22,MUTED)
text('TOTAL',X+11.5,18.43,2.65,22,MUTED,align='right')
manifest=json.loads((ROOT/'data/public-issues-v1.manifest.json').read_text())
lookup={s['path']:s for s in manifest['sources']}
source_order=[('OpenStreetMap iD','openstreetmap/iD'),('Hack for LA','hackforla/website'),('Open Food Facts','openfoodfacts/openfoodfacts-server'),('HOT Tasking Manager','hotosm/tasking-manager'),('FixMyStreet','mysociety/fixmystreet')]
for i,(name,path) in enumerate(source_order):
 s=lookup[path];y=19.2+i*1.13
 text(name,X,y,9.8,26,INK,True)
 text(f"{s['issues']:,}",X+11.3,y,2.85,26,INK,True,align='right')
 bw=14.15*s['issues']/8091
 rect(X,y+.55,bw,.26,LIGHT);rect(X,y+.55,bw*s['open_issues']/s['issues'],.26,TEAL)
text('Source snapshot: Oct. 29, 2026. Includes open and closed issues; pull requests excluded.',X,25.12,14.15,22,MUTED)
# Matching weights panel
MX=17.0;MW=13.6
heading('03','A score you can inspect',MX,15.33,MW)
text('Evidence-aware matching',MX,16.61,MW,33,N,True)
weights=[('Technical skills',60,TEAL),('Difficulty / experience',20,N),('Civic interests',15,'527A9C'),('Availability / effort',5,GOLD)]
for i,(label,value,color) in enumerate(weights):
 y=17.52+i*1.42
 text(label,MX,y,10.9,28,INK)
 text(f'{value}%',MX+10.8,y,2.8,30,color,True,align='right')
 rect(MX,y+.62,MW,.27,PALE);rect(MX,y+.62,MW*value/100,.27,color)
rect(MX,23.43,MW,2.67,PALE,r=.12)
text('Missing evidence stays unknown.',MX+.35,23.77,MW-.7,29,N,True)
text('AI-inferred skills count at half weight. Evidence coverage is shown separately from fit.',MX+.35,24.43,MW-.7,27,MUTED)
# Bottom visual: user workflow
heading('04','Find a cause. Make a contribution.',X,27.0,W)
steps=[('1','Build a profile','Skills + civic interests'),('2','Discover a fit','Compare match evidence'),('3','Work on GitHub','Follow source guidelines'),('4','Track progress','Record a submission')]
for i,(number,title,sub) in enumerate(steps):
 x=X+i*7.45
 rect(x,28.31,6.8,2.12,PALE,LINE,.14)
 text(number,x+.2,28.65,.65,38,TEAL,True)
 text(title,x+1,28.58,5.55,27,N,True)
 text(sub,x+.25,29.43,6.3,22,MUTED,align='center')
 if i<3:arrow(x+6.97,29.02,.3)
text('Bookmarks, messages and personal contribution history support follow-through.',X,30.87,W,28,MUTED)
# Right column editorial sections
heading('','Problem Statement',RX,6.32,RW)
text('Civic technology projects rely on volunteers to build and maintain tools that serve communities, but finding a suitable task can be difficult. Opportunities are scattered across GitHub repositories, and issue descriptions often contain technical jargon, incomplete requirements, or unclear explanations of the work involved. These barriers make it especially challenging for new contributors to understand a task, connect it to a civic cause, and determine whether their skills are a good fit. Civic Issue Matchmaker addresses this problem by bringing opportunities into one searchable platform, using AI to make issue descriptions easier to understand, and matching tasks with volunteers’ technical skills and civic interests while preserving access to the original source.',RX,7.55,RW,32,INK,False,1.22,h=7.15)
heading('','Results',RX,15.33,RW)
# Parallel result figures, from documented records only.
for x,num,label in [(RX,'5','civic-tech sources'),(RX+7.4,'2,220','cached AI records')]:
 text(num,x,16.6,6.9,64,N,True)
 text(label,x,17.7,6.9,26,MUTED)
text('Implemented',RX,18.75,RW,32,TEAL,True)
text('Explained recommendations, source filters, curator corrections, private bookmarks, messaging and contribution tracking.',RX,19.43,RW,32,INK)
text('78 backend tests + 12 browser workflows',RX,21.66,RW,30,N,True)
text('Reported passing Oct. 28, 2026; 5 PostgreSQL-only tests skipped. Build and lint checks passed.',RX,22.43,RW,26,MUTED)
heading('','Conclusions & Impact',RX,24.8,RW)
text('A practical bridge from technical skills to public-purpose software.',RX,26.05,RW,38,N,True)
text('One catalog connects contributors to infrastructure reporting, humanitarian mapping, open geographic data, food transparency and civic participation.',RX,27.95,RW,31,INK)
text('Next: measure recommendation usefulness with users, and complete load and accessibility evaluation.',RX,30.19,RW,28,TEAL,True)
# Template footer branding and compact provenance.
picture(fau,1.47,32.75,13.81,2.52)
text('SENIOR DESIGN\nSHOWCASE',39.2,32.95,7.3,35,N,True,1.12,align='right')
# Notes carry detailed provenance without cluttering the poster.
slide.notes_slide.notes_text_frame.text='''Sources: data/public-issues-v1.manifest.json (2026-10-29); README.md; docs/PROJECT_SCOPE.md; docs/AI_MATCHING.md; docs/REQUIREMENTS_STATUS.md and docs/IMPLEMENTATION_REVIEW.md (2026-10-28). All quantitative values are snapshot counts or historical verification records, not live measurements. Source bar lengths encode total issues; teal segments encode open issues. Cached AI records are not an accuracy metric. No measured usability, acceptance, AI accuracy, load, or accessibility rate is claimed. Team, advisor and sponsor confirmed by user on Nov. 8, 2026. Course facilitator names and official FAU artwork retained from supplied first-slide template. Showcase number omitted pending assignment. Sponsor is user-provided; source repositories are not implied sponsors or partners.'''
prs.core_properties.title='Civic Issue Matchmaker — Senior Design Showcase'
prs.core_properties.subject='48 × 36 inch landscape poster'
prs.core_properties.author='Group 26'
prs.save(OUT/'Civic_Issue_Matchmaker_Poster.pptx')
c.showPage();c.save()
print(f'Created PPTX + vector PDF; {len(slide.shapes)} editable objects; {len(checks)} text blocks checked.')
