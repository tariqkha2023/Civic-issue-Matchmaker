"""Create Demo 2 slides using the first demo's theme and logo. No credentials."""
from io import BytesIO
from pathlib import Path
import json
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt
from pptx.oxml.xmlchemy import OxmlElement

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).resolve().parent
SOURCE = ROOT / 'Civic Issue Matchmaker-First Demo Group26.pptx'
OUTPUT = ROOT / 'Civic Issue Matchmaker-Second Demo Group26.pptx'
p = Presentation(SOURCE)
logo = next(s.image.blob for s in p.slides[0].shapes if s.shape_type == 13)
for sid in list(p.slides._sldIdLst):
    p.part.drop_rel(sid.rId)
    p.slides._sldIdLst.remove(sid)
W, H = 13.333333, 7.5
NAVY, CREAM, GOLD = '12243A', 'F8F5EF', 'F2C44C'
BLUE, TEAL, INK, MUTED, WHITE, BORDER = '35638A', '26765C', '22364B', '596777', 'FFFFFF', 'E2DED5'

def color(c): return RGBColor.from_string(c)

def box(s, x, y, w, h, fill, border=None, rounded=False):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = color(fill)
    if border: sh.line.color.rgb = color(border); sh.line.width = Pt(.7)
    else: sh.line.fill.background()
    if rounded: sh.adjustments[0] = .08
    return sh

def text(s, x, y, w, h, content, size=18, fill=INK, bold=False, font='Aptos', align=PP_ALIGN.LEFT):
    sh = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = sh.text_frame; tf.clear(); tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(.015)
    tf.margin_top = tf.margin_bottom = Inches(.015)
    for i, line in enumerate(content.split('\n')):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align; para.space_after = Pt(4); para.line_spacing = 1.10
        run = para.add_run(); run.text = line
        run.font.name = font; run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = color(fill)
    return sh

def base(section, title, n):
    s = p.slides.add_slide(p.slide_layouts[0])
    box(s, 0, 0, W, H, CREAM); box(s, 0, 0, .16, H, GOLD)
    text(s, .63, .38, 11.8, .25, section, 11, BLUE, True)
    text(s, .63, .86, 12.05, .77, title, 28, NAVY, font='Georgia')
    footer(s,n)
    return s

def footer(s,n,dark=False):
    text(s,.65,7.13,10.8,.2,'EGN 4952C  |  Demo 2  |  Group 26  |  Status: November 15, 2026',9, 'B9C3D0' if dark else MUTED)
    text(s,12.05,7.08,.55,.28,f'{n:02}',10,'B9C3D0' if dark else MUTED,align=PP_ALIGN.RIGHT)

def note(s,content):
    notes=s.notes_slide
    if notes.notes_text_frame is None:
        shape=OxmlElement('p:sp')
        nv=OxmlElement('p:nvSpPr')
        props=OxmlElement('p:cNvPr'); props.set('id','99'); props.set('name','Speaker notes'); nv.append(props)
        nv.append(OxmlElement('p:cNvSpPr'))
        nvpr=OxmlElement('p:nvPr'); ph=OxmlElement('p:ph');ph.set('type','body');ph.set('idx','1');nvpr.append(ph);nv.append(nvpr)
        shape.append(nv);shape.append(OxmlElement('p:spPr'))
        tx=OxmlElement('p:txBody');tx.append(OxmlElement('a:bodyPr'));tx.append(OxmlElement('a:lstStyle'));tx.append(OxmlElement('a:p'));shape.append(tx)
        notes.shapes._spTree.append(shape)
    notes.notes_text_frame.text = content.strip()

def rule(s,x1,y1,x2,y2,c=GOLD):
    sh=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2));sh.line.color.rgb=color(c);sh.line.width=Pt(2)

def item(s,x,y,w,heading,body):
    text(s,x,y,w,.32,heading,18,NAVY,True)
    text(s,x,y+.42,w,.88,body,16,MUTED)

# 1 — Title, group and all team members.
s=p.slides.add_slide(p.slide_layouts[0])
box(s,0,0,W,H,NAVY);box(s,0,0,.16,H,GOLD)
text(s,.77,.68,8.9,.3,'EGN 4952C · ENGINEERING DESIGN 2',12,GOLD,True)
text(s,.75,1.33,8.7,1.55,'Civic Issue\nMatchmaker',42,WHITE,font='Georgia')
text(s,.80,3.18,9,.5,'Second Project Demo',23,'D7DEE8')
box(s,.80,3.95,.85,.05,GOLD)
text(s,.80,4.35,9.7,.4,'Group 26  |  Status as of November 15, 2026',19,WHITE,True)
text(s,.80,5.05,11.6,.83,'Davian Brooks · Michael Anstett · Tariq Khan\nAndre Walia · David Landivar',18,'CFD9E6')
text(s,.80,6.29,11.7,.42,'Real GitHub issues, explained recommendations, and contribution tracking.',16,'CFD9E6')
s.shapes.add_picture(BytesIO(logo),Inches(10.05),Inches(1.18),width=Inches(2.40))
footer(s,1,True)
note(s,"""\nWe are Group 26: Davian Brooks, Michael Anstett, Tariq Khan, Andre Walia and David Landivar. Civic Issue Matchmaker helps contributors find software tasks supporting civic causes. Our first demo used a sample collection. Today we can show the application working with five public GitHub repositories, task explanations, personal recommendations and contribution tracking.\n""")

# 2 — Objective and technical approach.
s=base('OBJECTIVE & TECHNICAL APPROACH','Match contributors with civic-tech issues',2)
text(s,.66,1.75,12,.63,'Find GitHub issues that fit a contributor’s skills and interests, and explain why they match.',20,INK)
steps=[('01','Profile','Skills and\ncivic interests'),('02','Collect','Five civic issue\ntrackers on GitHub'),('03','Interpret','Task summaries\nSkills + evidence'),('04','Match','Skills + interests\nExplained scores'),('05','Contribute','Open on GitHub\nSave and track')]
for i,(num,title,body) in enumerate(steps):
    x=.66+i*2.46
    box(s,x,2.63,2.23,2.35,WHITE,BORDER,True)
    text(s,x+.18,2.95,1.8,.3,num,14,BLUE,True)
    text(s,x+.18,3.40,1.85,.35,title,21,NAVY,font='Georgia')
    text(s,x+.18,3.98,1.89,.94,body,15,MUTED)
    if i<4: rule(s,x+2.25,3.73,x+2.42,3.73)
box(s,.66,5.21,12.05,1.24,NAVY,rounded=True)
text(s,.91,5.43,11.5,.4,'React / JSX  →  FastAPI domain services  →  SQLite',22,WHITE,True)
text(s,.91,5.98,11.5,.3,'Scheduled read-only GitHub sync · Optional operator-run AI processing · Offline cached browsing',14,'D7DEE8')
note(s,"""\nA contributor enters technical skills and civic interests. We collect public GitHub issues, store them in SQLite, and use saved issue interpretations to explain the work. The frontend is React and the backend is FastAPI.
The match compares skills and civic interests, with 80/20 weighting when both are available. Inferred skills have half the weight of stated or curator-reviewed skills. Unknown information stays unknown. The score explains the available evidence; it does not predict whether a contribution will be accepted.
GitHub synchronization and paid AI processing are operator actions. Browsing the saved collection does not make AI calls. Users save and track work here, then open the GitHub issue to contribute.\n""")

# 3 — Completed status and progress since the prior demonstration.
s=base('STATUS 1 OF 4 · COMPLETED SINCE DEMO 1','Five real repositories replace the sample dataset',3)
for x,value,label in [( .66,'21,558','public issues bundled'),(4.76,'3,539','open issues processed'),(8.86,'5','civic source repositories')]:
    box(s,x,1.94,3.84,1.16,WHITE,BORDER,True)
    text(s,x+.21,2.06,3.42,.55,value,31,NAVY,True)
    text(s,x+.21,2.67,3.42,.26,label,14,MUTED)
text(s,.70,3.47,4.0,.35,'DEMO 1',12,BLUE,True)
text(s,4.50,3.47,7.7,.35,'DEMO 2 · NOW IMPLEMENTED',12,BLUE,True)
rows=[('Sample civic issues','Complete public issue snapshot with source IDs, states and assignees'),('Claims / participation planned','Personal contribution states; multiple people may track one issue'),('Curator and admin tools planned','Scoped metadata corrections, source controls, role management and audit'),('Notifications / privacy planned','In-app messages and alerts, preferences, account export and deletion')]
for i,(before,after) in enumerate(rows):
    y=3.96+i*.53
    if i%2==0: box(s,.66,y-.04,12.05,.50,'EFECE5',rounded=True)
    text(s,.80,y,3.42,.4,before,14,MUTED)
    text(s,4.50,y,7.95,.42,after,15,INK)
text(s,.72,6.32,11.9,.5,'Sources: FixMyStreet · HOT Tasking Manager · OpenStreetMap iD · Open Food Facts · Hack for LA',13,BLUE,True)
note(s,"""\nThe largest change since Demo 1 is replacing sample data with five real civic repositories: FixMyStreet, HOT Tasking Manager, OpenStreetMap iD, Open Food Facts and Hack for LA.
The saved snapshot contains 21,558 issues, including 3,539 open issues. All open issues have a processing result: 2,389 interpretations passed validation and 1,150 use the original source information because the output was rejected. A validation pass is not independent confirmation of accuracy. Twenty issues also have researched project context and suggested skills.
The participation, curator, administration, messaging and privacy work that was planned in Demo 1 is now implemented. Several contributors can track the same issue; tracking does not reserve it on GitHub.\n""")

# 4 — Integrated prototype with current screenshot.
s=base('STATUS 2 OF 4 · COMPLETED FEATURES','Search, understand the task, and track progress',4)
item(s,.72,1.94,4.35,'Task explanations','Project context, task objective, suggested skills, supporting quotes and task questions.')
item(s,.72,3.47,4.35,'Search and tracking','Personal match explanations; search controls; save, track, start work and record submissions.')
item(s,.72,5.00,4.35,'Accounts and team tools','Curator corrections, source administration, messages, alerts and privacy controls.')
box(s,5.39,1.90,7.30,4.91,WHITE,BORDER,True)
s.shapes.add_picture(str(BASE/'Discover-Task-Evidence.png'),Inches(5.54),Inches(2.06),width=Inches(7.00))
text(s,5.55,6.78,7.0,.2,'Current prototype · OpenStreetMap iD issue #8695 · Saved public snapshot',10,MUTED)
note(s,"""\nThis is a screenshot of the running application showing OpenStreetMap iD issue 8695. It explains why the requested change matters, describes the work, and identifies questions to confirm with the source project. Suggested skills have reasons and supporting quotes.
For the live walkthrough, show the contributor profile, search for drainpipe in OpenStreetMap iD, and open issue 8695. Expand the skill evidence and match explanation. Then search frontend and compare results with suggested skills enabled and disabled. That setting changes retrieval, not the personal match score.
Save an issue, track it, and start work in My contributions. Open its GitHub link to show where the actual contribution happens. Then show curator corrections and administrator source status if time permits. The complete walkthrough fits within ten minutes: profile and discovery, three minutes; explanations and search controls, two minutes; tracking and GitHub, two minutes; curator, administration and privacy, two minutes; closing questions, one minute.\n""")

# 5 — Verification and implementation challenges.
s=base('STATUS 3 OF 4 · TESTING','Testing and technical challenges',5)
metrics=[(.66,'94','backend tests passed','5 legacy PostgreSQL checks skipped'),(4.76,'45','browser checks passed','Chromium, Firefox and WebKit'),(8.86,'500','active identities checked','32 parallel reads in an isolated database')]
for x,value,label,sub in metrics:
    box(s,x,1.92,3.84,1.57,WHITE,BORDER,True)
    text(s,x+.20,2.05,3.40,.55,value,32,NAVY,True)
    text(s,x+.20,2.69,3.40,.30,label,17,INK,True)
    text(s,x+.20,3.10,3.40,.25,sub,11.5,MUTED)
text(s,.72,3.92,11.8,.35,'CHALLENGE  →  HOW WE HANDLED IT',12,BLUE,True)
for y,h,b in [(4.43,'Incomplete issue metadata','Grounded explanations and visible skill evidence; unknown values stay unknown.'),(5.12,'Source changes and failures','Stable source IDs, staged synchronization, cache invalidation and curator overlays.'),(5.81,'Avoiding repeated AI costs','Explicit budgeted runs, reusable public caches and verified offline setup.')]:
    text(s,.76,y,3.65,.47,h,16,NAVY,True);text(s,4.52,y,7.90,.48,b,16,MUTED)
note(s,"""\nThe backend suite passes 94 tests; five legacy PostgreSQL tests are skipped because this prototype uses SQLite. The 45 browser checks cover Chromium at three screen sizes, Firefox and WebKit. Automated accessibility checks found low-contrast labels, which we corrected. Manual accessibility review is still outstanding.
We also checked 500 active session identities under 32 parallel reads without losing sessions or mixing identities. This is separate from the sustained-load test we still need.
The main challenges were incomplete issue descriptions, preserving data when source content changes, and avoiding repeated AI costs. We addressed these with grounded explanations, source identities and staged updates, curator corrections, and reusable caches. A fresh offline setup restored the public data and cache without including private accounts or credentials.\n""")

# 6 — Project work in progress and remaining tests.
s=base('STATUS 4 OF 4 · IN PROGRESS & REMAINING','What we are working on next',6)
columns=[
    (.66,'IN PROGRESS',BLUE,[
        ('Task descriptions','Refining explanations and making suggested skills easier to distinguish from requirements.'),
        ('Match explanations','Checking whether the skills and match explanations make sense for real issues.')]),
    (4.76,'PERFORMANCE TESTING',TEAL,[
        ('Sustained load','Measure response times with 100 active users over 30 minutes.'),
        ('Larger collections','Test synchronization with 50 repositories and 100,000 issue records.')]),
    (8.86,'USER TESTING',NAVY,[
        ('First-time users','Run the five-person study: create a profile, find an issue, and open it on GitHub.'),
        ('Quality and access','Review suggested skills for accuracy; complete manual keyboard and screen-reader checks.')])]
for x,heading,c,items in columns:
    box(s,x,1.96,3.84,4.72,WHITE,BORDER,True)
    box(s,x,1.96,3.84,.12,c)
    text(s,x+.22,2.28,3.37,.38,heading,12,c,True)
    for j,(h,b) in enumerate(items):
        y=3.02+j*1.85
        text(s,x+.22,y,3.37,.43,h,18,NAVY,True)
        text(s,x+.22,y+.52,3.37,1.02,b,15,MUTED)
text(s,.74,6.82,11.9,.22,'The prototype runs locally. GitHub remains the source for issue state, assignment, and contribution acceptance.',11,BLUE)
note(s,"""
We are still refining the task explanations and reviewing whether the suggested skills make sense for the actual work. The features are connected, but the formal quality tests are not all finished.
We still need the sustained load test with 100 active users and the larger synchronization test with 50 repositories and 100,000 records. The existing session test checks 500 active identities under 32 parallel reads; it does not replace those measurements.
For user testing, five people unfamiliar with the application will create a profile, find an issue and open the GitHub posting. Our target is four of five finishing within five minutes without help. We also need a manual review of suggested-skill accuracy and keyboard and screen-reader access.
The application currently runs locally. Source updates, cached explanations and private tracking are kept separate, and GitHub remains authoritative for assignment and acceptance.
""")

p.core_properties.title='Civic Issue Matchmaker — Demo 2 — Group 26'
p.core_properties.subject='Project Status Report and Live Prototype Demonstration'
p.core_properties.author='Group 26: Davian Brooks, Michael Anstett, Tariq Khan, Andre Walia, David Landivar'
p.core_properties.keywords='EGN 4952C, Demo 2, Group 26, project status, live prototype'
p.core_properties.comments='Prepared from the first-demo presentation and verified project status as of November 15, 2026.'
p.save(OUTPUT)

# Reviewable structural validation. Rendered layout is also checked separately.
reopened=Presentation(OUTPUT)
assert len(reopened.slides)==6
assert reopened.slide_width==p.slide_width and reopened.slide_height==p.slide_height
for index,slide in enumerate(reopened.slides,1):
    assert slide.has_notes_slide
    assert len(slide.notes_slide.notes_text_frame.text)>100
    for shape in slide.shapes:
        assert shape.left>=0 and shape.top>=0, (index,shape.name)
        assert shape.left+shape.width <= reopened.slide_width+1000, (index,shape.name,'right edge')
        assert shape.top+shape.height <= reopened.slide_height+1000, (index,shape.name,'bottom edge')
slide_text='\n'.join(s.text for slide in reopened.slides for s in slide.shapes if s.has_text_frame)
assert 'First Project Demo' not in slide_text and 'Prototype video' not in slide_text
assert all(name in slide_text for name in ['Davian Brooks','Michael Anstett','Tariq Khan','Andre Walia','David Landivar'])
assert all(term in slide_text for term in ['Group 26','OBJECTIVE','IN PROGRESS','REMAINING','94','45','21,558','3,539'])
(BASE/'VALIDATION.json').write_text(json.dumps({'file':OUTPUT.name,'slides':6,'required_title_and_team':True,'objective_and_approach':True,'status_slides':4,'speaker_notes_all_slides':True,'out_of_bounds_shapes':0,'original_reference_unchanged':str(SOURCE.name),'status_date':'2026-11-15'},indent=2)+'\n')
print(OUTPUT)
