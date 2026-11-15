const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:2100},deviceScaleFactor:2});
 const creds=JSON.parse(fs.readFileSync('/tmp/civic-poster-credentials.json','utf8'));
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:5185/#/login');
 await page.getByLabel('Email',{exact:true}).fill(creds.email);
 await page.getByLabel('Password',{exact:true}).fill(creds.password);
 await page.getByRole('button',{name:'Login',exact:true}).last().click();
 await page.getByRole('heading',{name:'Discover civic-tech issues'}).waitFor();
 await page.locator('.discoverIssue').first().waitFor();
 const recs=await page.evaluate(async()=>await (await fetch('/api/recommendations?page=1&status=open&sort=compatibility')).json());
 console.log(JSON.stringify(recs.items.slice(0,6).map(t=>({title:t.title,score:t.score,id:t.id,repository:t.repository})),null,2));
 const firstBox=await page.locator('.discoverIssue').first().boundingBox();
 await page.screenshot({path:'showcase-poster/Site_Discovery_Fresh.png',clip:{x:0,y:0,width:1440,height:Math.min(2100,Math.ceil(firstBox.y+firstBox.height+24))}});
 // Native element screenshot captures the first real recommendation at high resolution.
 await page.locator('.discoverIssue').first().screenshot({path:'showcase-poster/Site_Issue_Fresh.png'});
 await page.getByRole('button',{name:recs.items[0].title,exact:true}).click();
 await page.getByRole('heading',{name:recs.items[0].title,exact:true}).waitFor();
 await page.getByText('Match details and source metadata',{exact:true}).click();
 await page.locator('.discoverIssue').screenshot({path:'showcase-poster/Site_Evidence_Fresh.png'});
 fs.writeFileSync('showcase-poster/CAPTURE_RECORD.json',JSON.stringify({captured_at:new Date().toISOString(),origin:'http://127.0.0.1:5185',data:'Bundled public GitHub snapshot; separate showcase profile',issue:{title:recs.items[0].title,url:recs.items[0].url,score:recs.items[0].score},browser_errors:errors},null,2));
 console.log('Fresh screenshots captured; browser errors:',errors.length);
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
