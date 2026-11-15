const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try {
 const owner=await browser.newPage({viewport:{width:1280,height:1000}});const errors=[];owner.on('pageerror',e=>errors.push(e.message));
 const origin=process.env.BRIEF_URL||'http://127.0.0.1:8090';await owner.goto(origin);await owner.locator('#access-key').fill(process.env.BRIEF_OWNER_KEY);await owner.getByRole('button',{name:'Open workspace'}).click();await owner.locator('#owner-panel').waitFor({state:'visible'});
 await owner.locator('#title').fill('Studio website refresh');await owner.locator('#labels').fill('Brand assets');await owner.getByRole('button',{name:'Create request',exact:true}).click();await owner.locator('#handoff').waitFor({state:'visible'});
 const id=await owner.locator('#share-id').inputValue(),token=await owner.locator('#share-key').inputValue();
 const client=await browser.newPage();await client.goto(origin+'/?client=1');await client.locator('#request-id').fill(id);await client.locator('#access-key').fill(token);await client.getByRole('button',{name:'Open workspace'}).click();await client.locator('#detail').waitFor({state:'visible'});
 await client.getByLabel('Your response').fill('Our first brand direction');await client.getByRole('button',{name:'Submit response'}).click();await client.getByText('Revision 1',{exact:true}).waitFor();
 await owner.getByRole('button',{name:'Studio website refresh',exact:true}).last().click();await owner.getByLabel('Review note').fill('Please attach the logo file');await owner.getByRole('button',{name:'Request changes',exact:true}).click();await owner.getByText('v1 · changes requested — Please attach the logo file').waitFor();
 // Re-open with the same client key to fetch the latest review.
 await client.reload();await client.locator('#request-id').fill(id);await client.locator('#access-key').fill(token);await client.getByRole('button',{name:'Open workspace'}).click();await client.getByText('v1 · changes requested — Please attach the logo file').waitFor();
 await client.locator('input[type=file]').setInputFiles({name:'logo.txt',mimeType:'text/plain',buffer:Buffer.from('approved file bytes')});await client.getByRole('button',{name:'Submit response'}).click();await client.getByText('Revision 2',{exact:true}).waitFor();
 await owner.getByRole('button',{name:'Studio website refresh',exact:true}).last().click();await owner.getByRole('button',{name:'Approve revision'}).click();await owner.getByText('1 of 1 approved',{exact:true}).waitFor();
 const download=owner.waitForEvent('download');await owner.getByRole('button',{name:'Export history'}).click();const exported=await download;const stream=await exported.createReadStream();let raw='';for await(const chunk of stream)raw+=chunk;assert.equal(JSON.parse(raw).items[0].history.length,2);
 await owner.screenshot({path:'/tmp/brief-workspace-desktop.png',fullPage:true});await owner.setViewportSize({width:390,height:844});await owner.screenshot({path:'/tmp/brief-workspace-mobile.png',fullPage:true});assert.equal(await owner.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 owner.on('dialog',dialog=>dialog.accept());await owner.getByRole('button',{name:'Replace client key'}).click();await owner.waitForFunction(old=>document.querySelector('#share-key').value!==old,token);
 const response=await client.request.get(origin+'/api/requests/'+id,{headers:{Authorization:'Bearer '+token}});assert.equal(response.status(),400);assert.deepEqual(errors,[]);
 console.log('PASS: owner/client text → change request → file → approval → history export → key revocation; desktop/mobile screenshots captured');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
