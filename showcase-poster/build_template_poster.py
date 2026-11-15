"""Populate the supplied poster template without changing its text geometry/styles."""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
import json
from pptx import Presentation
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches,Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from PIL import Image
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent
P=Presentation(ROOT/'SENIOR SHOWCASE POSTER TEMPLATE UPDATED 8-6-2026.pptx')
for sid in list(P.slides._sldIdLst)[1:]:
 P.part.drop_rel(sid.rId);P.slides._sldIdLst.remove(sid)
S=P.slides[0];original=list(S.shapes)
# Capture geometry and typography before changing content.
def signature(shape):
 return {'geometry':[shape.left,shape.top,shape.width,shape.height,shape.rotation],
 'bodyPr':shape.text_frame._txBody.bodyPr.xml if shape.has_text_frame else None,
 'first_rPr':shape.text_frame.paragraphs[0].runs[0]._r.rPr.xml if shape.has_text_frame and shape.text_frame.paragraphs[0].runs else None}
before={str(i):signature(s) for i,s in enumerate(original)}
def replace(i,txt):
 shape=original[i];tx=shape.text_frame._txBody
 proto=deepcopy(shape.text_frame.paragraphs[0]._p)
 runproto=deepcopy(shape.text_frame.paragraphs[0].runs[0]._r)
 for p in list(tx):
  if p.tag.endswith('}p'):tx.remove(p)
 for j,para in enumerate(txt.split('\n')):
  p=deepcopy(proto)
  for child in list(p):
   if child.tag.rsplit('}',1)[-1] not in ['pPr','endParaRPr']:p.remove(child)
  run=deepcopy(runproto);run.find('{http://schemas.openxmlformats.org/drawingml/2006/main}t').text=para
  end=p.find('{http://schemas.openxmlformats.org/drawingml/2006/main}endParaRPr')
  if end is not None:p.insert(list(p).index(end),run)
  else:p.append(run)
  tx.append(p)
replace(1,'Civic Issue Matchmaker')
replace(3,'Davian Brooks\nMichael Anstett\nTariq Khan · Andre Walia\nDavid Landivar')
replace(5,'Dr. Hari Kalva')
replace(8,'Sponsored by: Code for America')
replace(13,'') # No assigned showcase project number supplied.
replace(23,'') # Template instruction is not poster content.
replace(7,'Civic technology projects rely on volunteers, but finding a suitable task is difficult. Opportunities are scattered across GitHub repositories, with technical jargon and incomplete requirements that make it hard to assess fit. Civic Issue Matchmaker brings tasks into one searchable platform, uses AI to clarify requirements, and matches opportunities with volunteers’ technical skills and civic interests while preserving the original source.')
replace(10,'The platform provides searchable civic-tech issues, explained recommendations, curator corrections and personal contribution tracking.\nThe bundled snapshot contains 21,558 public GitHub issues from five projects and 2,220 cached AI records.\nRecorded verification: 78 backend tests and 12 browser workflows passed; five PostgreSQL-only tests were skipped.')
replace(11,'Civic Issue Matchmaker connects technical skills with public-purpose software through one searchable catalog. Contributors can inspect match evidence and follow the original issue to participate.\nAI-inferred requirements are labeled, weighted conservatively and open to curator correction.\nNext steps are user evaluation of recommendation usefulness, load testing and a full accessibility review.')
# Replace image-slot content only; all seven original slot rectangles stay fixed.
slots={i:(s.left,s.top,s.width,s.height) for i,s in enumerate(original) if s.shape_type==13}
for i in slots:
 s=original[i];s._element.getparent().remove(s._element)
BLACK='000000';NAVY='003366';GRAY='E7EBEF';WHITE='FFFFFF'
def box(x,y,w,h,color):
 s=S.shapes.add_shape(MSO_SHAPE.RECTANGLE,int(x),int(y),int(w),int(h))
 s.fill.solid();s.fill.fore_color.rgb=RGBColor.from_string(color);s.line.fill.background();return s

def label(txt,x,y,w,h,size=39.6,bold=False):
 s=S.shapes.add_textbox(int(x),int(y),int(w),int(h));tf=s.text_frame
 tf.margin_left=tf.margin_right=0;tf.margin_top=tf.margin_bottom=0;tf.word_wrap=True
 for n,line in enumerate(txt.split('\n')):
  p=tf.paragraphs[0] if n==0 else tf.add_paragraph();p.text=line;p.font.name='Lato';p.font.size=Pt(size);p.font.color.rgb=RGBColor.from_string(BLACK);p.font.bold=bold
 return s

def ip(v):return Inches(v)
# All visual assets below are native, editable PowerPoint objects. No image generation.
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.chart.data import ChartData
TEAL='168C91';PURPLE='8064AE';AMBER='E9AB38';CORAL='E66D66'
PASTELS=['E5F3F1','EEE8F6','FFF3DA','FBEAE7']
def shape(kind,x,y,w,h,color):
 z=S.shapes.add_shape(kind,int(x),int(y),int(w),int(h));z.fill.solid();z.fill.fore_color.rgb=RGBColor.from_string(color);z.line.fill.background();return z

def line(x1,y1,x2,y2,color,width=5):
 z=S.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,int(x1),int(y1),int(x2),int(y2));z.line.color.rgb=RGBColor.from_string(color);z.line.width=Pt(width);return z

def circle(x,y,d,color):return shape(MSO_SHAPE.OVAL,x,y,d,d,color)
def check(x,y,d,color=WHITE):
 line(x+d*.21,y+d*.51,x+d*.43,y+d*.72,color,5)
 line(x+d*.43,y+d*.72,x+d*.81,y+d*.29,color,5)
def person(x,y,d,color=WHITE):
 circle(x+d*.37,y+d*.15,d*.27,color)
 shape(MSO_SHAPE.ARC,x+d*.22,y+d*.49,d*.56,d*.38,color)
 # Rounded body is a simple, editable silhouette.
 shape(MSO_SHAPE.ROUNDED_RECTANGLE,x+d*.24,y+d*.5,d*.52,d*.31,color)
def glyph(kind,x,y,d):
 if kind=='profile':person(x,y,d)
 elif kind=='search':
  z=circle(x+d*.19,y+d*.16,d*.44,WHITE)
  circle(x+d*.25,y+d*.22,d*.32,TEAL)
  line(x+d*.59,y+d*.58,x+d*.82,y+d*.81,WHITE,7)
 elif kind=='evidence':
  box(x+d*.28,y+d*.19,d*.43,d*.62,WHITE)
  for j in range(3):box(x+d*.36,y+d*(.32+j*.15),d*.27,d*.045,PURPLE)
 elif kind=='contribute':check(x,y,d)
# Graphic 1: a hub diagram showing the product idea, instead of a screenshot.
x,y,w,h=slots[15];box(x,y,w,h,WHITE)
label('Your skills. A civic purpose.',x+ip(.3),y+ip(.25),w-ip(.6),ip(1),50.4)
label('Technical skills',x+ip(.4),y+ip(1.65),ip(5.0),ip(.85),39.6,True)
label('Civic interests',x+ip(10.0),y+ip(1.65),ip(4.6),ip(.85),39.6,True)
# Draw connections behind nodes so every node remains clear.
for j,color in enumerate([TEAL,PURPLE,AMBER]):
 yy=y+ip(3.05+j*2.18)
 line(x+ip(4.55),yy+ip(.6),x+ip(6.2),y+ip(5.7),color,5)
 line(x+ip(8.75),y+ip(5.7),x+ip(10.35),yy+ip(.6),color,5)
# Central matching hub: colored concentric shapes with unchanged black typography.
circle(x+ip(5.15),y+ip(3.45),ip(4.6),PASTELS[0])
circle(x+ip(5.48),y+ip(3.78),ip(3.94),'CBE7E3')
label('Find\nyour fit',x+ip(6.05),y+ip(4.75),ip(3.05),ip(2.1),50.4,True)
for j,(skill,cause,color,pale) in enumerate(zip(['Code','Design','Write'],['Mapping','Food data','Civic tools'],[TEAL,PURPLE,AMBER],PASTELS)):
 yy=y+ip(3.05+j*2.18)
 shape(MSO_SHAPE.ROUNDED_RECTANGLE,x+ip(.35),yy,ip(4.3),ip(1.28),pale)
 box(x+ip(.35),yy,ip(.13),ip(1.28),color)
 label(skill,x+ip(.7),yy+ip(.26),ip(3.6),ip(.8),39.6)
 shape(MSO_SHAPE.ROUNDED_RECTANGLE,x+ip(10.3),yy,ip(4.3),ip(1.28),pale)
 box(x+ip(14.47),yy,ip(.13),ip(1.28),color)
 label(cause,x+ip(10.6),yy+ip(.26),ip(3.75),ip(.8),39.6)
label('One place to find a useful contribution.',x+ip(.4),y+ip(10.1),w-ip(.8),ip(.9),39.6)
# Graphic 2: color-coded evidence sources, retaining the accepted explanation.
x,y,w,h=slots[16];box(x,y,w,h,WHITE)
label('Evidence source breakdown',x+ip(.3),y+ip(.25),w-ip(.6),ip(1),50.4)
for j,(title,body,color,pale,kind) in enumerate([
 ('Stated or reviewed','Supported by source evidence\nor curator corrections.',TEAL,PASTELS[0],'contribute'),
 ('AI-inferred','Labeled suggestions count\nat half weight.',PURPLE,PASTELS[1],'evidence'),
 ('Unknown','Missing evidence stays unknown;\ncoverage is separate from fit.',AMBER,PASTELS[2],'unknown')]):
 yy=y+ip(1.8+j*3.05)
 shape(MSO_SHAPE.ROUNDED_RECTANGLE,x+ip(.25),yy,w-ip(.5),ip(2.67),pale)
 circle(x+ip(.55),yy+ip(.65),ip(1.35),color)
 if kind=='unknown':
  for k in range(3):circle(x+ip(.83+k*.28),yy+ip(1.24),ip(.12),WHITE)
 else:glyph(kind,x+ip(.55),yy+ip(.65),ip(1.35))
 label(title,x+ip(2.2),yy+ip(.31),w-ip(2.8),ip(.8),39.6,True)
 label(body,x+ip(2.2),yy+ip(1.14),w-ip(2.8),ip(1.4),39.6)
# Graphic 3: editable circular composition of the actual model weights.
x,y,w,h=slots[14];box(x,y,w,h,WHITE)
label('How matching works',x+ip(.3),y+ip(.25),w-ip(.6),ip(.95),50.4)
data=ChartData();data.categories=['Skills','Experience','Interests','Availability'];data.add_series('Model weights',[60,20,15,5])
chart=S.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT,x+ip(.05),y+ip(1.65),ip(8.5),ip(8.5),data).chart
chart.has_legend=False;chart.has_title=False
chart.chart_style=10
plot=chart.plots[0];plot.hole_size=68;plot.first_slice_angle=270;plot.has_data_labels=False
for pt,color in zip(chart.series[0].points,[TEAL,NAVY,PURPLE,AMBER]):
 pt.format.fill.solid();pt.format.fill.fore_color.rgb=RGBColor.from_string(color);pt.format.line.color.rgb=RGBColor.from_string(WHITE);pt.format.line.width=Pt(4)

label('Match\nfactors',x+ip(2.57),y+ip(4.95),ip(3.5),ip(2.1),50.4,True)
for j,(name,value,color) in enumerate([('Skills',60,TEAL),('Experience',20,NAVY),('Interests',15,PURPLE),('Availability',5,AMBER)]):
 yy=y+ip(2.4+j*1.8)
 circle(x+ip(8.75),yy+ip(.18),ip(.4),color)
 label(f'{value}%  {name}',x+ip(9.4),yy,ip(5.25),ip(1.45),39.6)
label('Known evidence earns points.\nMissing factors do not inflate the score.',x+ip(.3),y+ip(10.1),w-ip(.6),ip(1.5),39.6)
# Four original small slots: colored workflow panels with native shape icons.
for j,(i,title,body,kind,color) in enumerate([
 (17,'1. Profile','Set technical skills\nand civic interests.','profile',TEAL),
 (19,'2. Discover','Search tasks across\ncivic-tech projects.','search',TEAL),
 (18,'3. Inspect','Review requirements\nand match evidence.','evidence',PURPLE),
 (20,'4. Contribute','Open the source issue\nand track progress.','contribute',CORAL)]):
 x,y,w,h=slots[i]
 shape(MSO_SHAPE.ROUNDED_RECTANGLE,x,y,w,h,PASTELS[j])
 circle(x+ip(.35),y+ip(.5),ip(1.35),color);glyph(kind,x+ip(.35),y+ip(.5),ip(1.35))
 label(title,x+ip(1.96),y+ip(.63),w-ip(2.2),ip(1.55),50.4)
 label(body,x+ip(.4),y+ip(2.45),w-ip(.8),ip(2.5),39.6)
 box(x+ip(.4),y+h-ip(.49),w-ip(.8),ip(.09),color)

# Assert all existing text styles, colors, and boxes are unchanged.
for i,s in enumerate(original):
 if s.has_text_frame:
  after=signature(s)
  assert before[str(i)]==after,(i,before[str(i)],after)
full_statement='Civic technology projects rely on volunteers to build and maintain tools that serve communities, but finding a suitable task can be difficult. Opportunities are scattered across GitHub repositories, and issue descriptions often contain technical jargon, incomplete requirements, or unclear explanations of the work involved. These barriers make it especially challenging for new contributors to understand a task, connect it to a civic cause, and determine whether their skills are a good fit. Civic Issue Matchmaker addresses this problem by bringing opportunities into one searchable platform, using AI to make issue descriptions easier to understand, and matching tasks with volunteers’ technical skills and civic interests while preserving access to the original source.'
S.notes_slide.notes_text_frame.text='Original full user-provided problem statement:\n'+full_statement+'\n\nPoster copy is shortened to fit fixed template boxes without modifying font settings. All original text box geometry, body properties, first-run typography and colors are preserved. Original master/layout artwork is unchanged. Screenshot removed. All new visuals are native editable PowerPoint shapes and an editable doughnut chart. No image generation used. Colored fills distinguish diagram categories; font colors remain black, matching the template. Data counts: data/public-issues-v1.manifest.json, Oct.29,2026. Recorded tests: docs/REQUIREMENTS_STATUS.md, Oct.28,2026. No measured accuracy or usability improvement claimed. Showcase number not supplied; field blank.'
P.save(BASE/'Civic_Issue_Matchmaker_Poster.pptx')
(BASE/'TEMPLATE_VALIDATION.json').write_text(json.dumps({'original_text_styles_and_geometry_preserved':True,'template_image_slots':{str(i):list(g) for i,g in slots.items()},'original_text_signatures':before},indent=2))
print('Created poster directly from supplied template. Original text geometry and formatting verified unchanged.')
