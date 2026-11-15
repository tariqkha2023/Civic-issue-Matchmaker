"""Create three alternate posters with contributor-focused editable infographics."""
from pathlib import Path
BASE=Path(__file__).parent
source=(BASE/'build_poster.py').read_text()
start=source.index("heading('01','From scattered issues")
end=source.index('# Right column editorial sections',start)
variants={
'01_understand_the_issue':r'''
heading('01','Turn a technical issue into a clear first step',X,6.32,W)
text('ILLUSTRATIVE EXAMPLE · not a quoted source issue',X,7.54,W,24,MUTED)
rect(X,8.42,13.8,6.06,PALE,LINE,.16)
text('ORIGINAL ISSUE',X+.4,8.82,13,25,MUTED,True)
text('Fix focus loss after\nasync panel refresh',X+.4,9.6,13,45,N,True)
text('“After the fetch resolves, the component remounts and focus falls back to the document body.”',X+.4,11.33,13,32,INK)
arrow(X+14.12,10.9,.65)
rect(X+15.3,8.42,13.85,6.06,'EAF5F4',LINE,.16)
text('CLEARER TASK EXPLANATION',X+15.7,8.82,13,25,TEAL,True)
text('Keep keyboard users\nin the right place',X+15.7,9.6,13,45,N,True)
text('When the panel reloads, keep the keyboard cursor on the control the person was using.',X+15.7,11.33,13,32,INK)
text('AI-assisted interpretation supports understanding; the original GitHub issue stays accessible.',X,14.88,W,27,MUTED)
heading('02','Connect the task to a public purpose',X,16.12,W)
causes=[('FixMyStreet','Public infrastructure','Help communities report local problems.'),('HOT Tasking Manager','Humanitarian mapping','Support collaborative mapping work.'),('OpenStreetMap iD','Open geographic data','Improve tools for community map editing.'),('Open Food Facts','Food transparency','Support access to food-product information.'),('Hack for LA','Civic participation','Help volunteers build public-interest tools.')]
for i,(name,cause,desc) in enumerate(causes):
 x=X+(i%3)*9.95;y=17.53+(i//3)*3.42
 rect(x,y,9.25,3.02,PALE,LINE,.12)
 text(cause.upper(),x+.28,y+.3,8.69,22,TEAL,True)
 text(name,x+.28,y+.91,8.69,33,N,True)
 text(desc,x+.28,y+1.66,8.69,26,INK)
text('Choose a cause. Then find a task that fits your skills.',X+20,21.48,9.1,35,N,True)
heading('03','A useful recommendation answers three questions',X,25.3,W)
for i,(title,body) in enumerate([('Can I do it?','See relevant skills, difficulty and missing information.'),('Why does it matter?','Understand the civic project behind the task.'),('What is next?','Open the source issue and follow its contribution process.')]):
 x=X+i*9.95
 rect(x,26.68,9.25,4.45,PALE,LINE,.12)
 text(title,x+.38,27.1,8.49,38,TEAL,True)
 text(body,x+.38,28.18,8.49,32,INK)
''',
'02_explain_the_match':r'''
heading('01','Show why a task fits—not just a percentage',X,6.32,W)
text('ILLUSTRATIVE PROFILE + TASK · arithmetic example, not a measured outcome',X,7.55,W,24,MUTED)
for x,title,lines in [(X,'Contributor profile',[('Skills','JavaScript + accessibility'),('Experience','Beginner'),('Civic interest','Open geographic data')]),(X+15.3,'Example issue',[('Task','Improve keyboard navigation'),('Requirements','JavaScript + accessibility'),('Project purpose','Community mapping')])]:
 rect(x,8.47,13.85,5.89,PALE,LINE,.14)
 text(title,x+.4,8.86,13.05,40,N,True)
 for i,(label,value) in enumerate(lines):
  y=9.98+i*1.25
  text(label.upper(),x+.4,y,13.05,21,TEAL,True)
  text(value,x+.4,y+.42,13.05,30,INK)
arrow(X+14.22,10.85,.55)
heading('02','Follow the evidence behind the score',X,15.5,W)
# Cumulative score illustration on a fixed 100-point scale.
text('Each known matching factor adds points. Missing effort adds zero.',X,16.75,W,31,MUTED)
rows=[('Skills match',60,TEAL),('Experience aligns',20,N),('Civic interest aligns',15,'527A9C'),('Effort unknown',0,GOLD)]
cumulative=0
for i,(label,points,color) in enumerate(rows):
 y=17.96+i*1.55
 text(label,X,y,9.2,31,INK,True)
 rect(X+9.6,y+.13,15.2,.43,PALE)
 if cumulative:rect(X+9.6,y+.13,15.2*cumulative/100,.43,LINE)
 if points:rect(X+9.6+15.2*cumulative/100,y+.13,15.2*points/100,.43,color)
 cumulative+=points
 text(f'+{points}',X+25.4,y,3.75,34,color,True,align='right')
rect(X,24.51,W,1.66,N,r=.12)
text('95 / 100 illustrative fit',X+.4,24.89,13.6,44,WHITE,True)
text('Effort remains unknown; fit is not acceptance.',X+14.3,25.01,14.4,28,WHITE)
heading('03','Make uncertainty visible',X,27.07,W)
for i,(title,body) in enumerate([('Stated or reviewed','Requirements supported by issue evidence or curator review.'),('AI-inferred','Clearly labeled and counted at half weight.'),('Not enough evidence','Missing issue skills produce “Limited information,” not an inflated score.')]):
 x=X+i*9.95
 rect(x,28.42,9.25,3.2,PALE,LINE,.12)
 text(title,x+.32,28.77,8.61,32,TEAL,True)
 text(body,x+.32,29.57,8.61,27,INK)
''',
'03_contributor_journey':r'''
heading('01','From “Where do I start?” to a concrete task',X,6.32,W)
text('A contributor journey built around understanding, fit and follow-through.',X,7.55,W,32,MUTED)
journey=[('01','Bring your skills','Set technical skills, interests, experience and weekly availability.'),('02','Explore civic causes','Search across public-interest software projects in one catalog.'),('03','Understand the work','Inspect source details, AI-extracted requirements and match explanations.'),('04','Take the next step','Open the original issue, follow project guidance and track your contribution.')]
for i,(number,title,body) in enumerate(journey):
 x=X+(i%2)*15.3;y=8.76+(i//2)*4.03
 rect(x,y,13.85,3.56,PALE,LINE,.13)
 text(number,x+.34,y+.37,1.2,43,TEAL,True)
 text(title,x+1.78,y+.4,11.6,35,N,True)
 text(body,x+.4,y+1.43,13.05,31,INK)
heading('02','Three barriers. Three design responses.',X,17.32,W)
for i,(problem,solution) in enumerate([('Scattered repositories','One searchable catalog'),('Unclear requirements','AI-assisted evidence + curator review'),('Uncertain fit','Profile-based, explained recommendations')]):
 y=18.82+i*1.76
 rect(X,y,12.6,1.32,PALE,r=.1)
 text(problem,X+.35,y+.35,11.9,32,MUTED,True)
 arrow(X+13.2,y+.38,.55)
 rect(X+14.35,y,14.8,1.32,'EAF5F4',r=.1)
 text(solution,X+14.7,y+.31,14.1,29,TEAL,True)
heading('03','AI assistance with a human review path',X,24.95,W)
stages=[('Read','Public issue text'),('Extract','Stated + inferred skills'),('Review','Curator corrections'),('Explain','Visible fit + coverage')]
for i,(title,body) in enumerate(stages):
 x=X+i*7.45
 rect(x,26.39,6.8,2.65,PALE,LINE,.12)
 text(title,x+.3,26.82,6.2,37,N,True)
 text(body,x+.3,27.74,6.2,26,INK)
 if i<3:arrow(x+6.98,27.41,.29)
rect(X,29.69,W,1.56,N,r=.12)
text('The contributor can inspect the evidence and return to the original issue.',X+.4,30.11,W-.8,32,WHITE,True,align='center')
'''
}
for name,visual in variants.items():
 out=BASE/'variants'/name;out.mkdir(parents=True,exist_ok=True)
 code=source[:start]+visual+'\n'+source[end:]
 code=code.replace('OUT=Path(__file__).resolve().parent',f'OUT=Path({str(out.resolve())!r})')
 code=code.replace("Source bar lengths encode total issues; teal segments encode open issues.","Contributor-focused infographics replace issue-state charts. Any example tasks, profiles and scores are explicitly illustrative; they are not measured outcomes.")
 exec(compile(code,str(BASE/'build_poster.py'),'exec'),{'__file__':str((BASE/'build_poster.py').resolve()),'__name__':'__main__'})
 print(name)
