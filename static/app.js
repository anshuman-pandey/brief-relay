'use strict';
const $=id=>document.getElementById(id);
let key='',role='owner',requestId='',current=null;
const show=(id,yes)=>$(id).hidden=!yes;
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const notify=text=>I18n.text($('notice'),text);
const ui=(tag,source,cls,values={})=>{const n=node(tag,undefined,cls);I18n.text(n,source,values);return n;};
async function api(path,{data,form,download}={}){
 const headers={Authorization:`Bearer ${key}`};if(data!==undefined)headers['Content-Type']='application/json';
 const response=await fetch(path,{method:data!==undefined||form?'POST':'GET',headers,body:form|| (data!==undefined?JSON.stringify(data):undefined)});
 if(!response.ok){let error;try{error=(await response.json()).error;}catch{error='The server could not complete this request.';}throw Error(error);}
 return download?response.blob():response.json();
}
const base=()=>`/api/${role==='owner'?'owner/':''}requests/${encodeURIComponent(requestId)}`;
async function action(fn,button){notify('');if(button)button.disabled=true;try{await fn();}catch(e){notify(e.message);}finally{if(button)button.disabled=false;}}
function button(text,fn,values){const b=ui('button',text,undefined,values);b.type='button';b.onclick=()=>action(fn,b);return b;}
async function saveFile(path,name){const blob=await api(path,{download:true});const url=URL.createObjectURL(blob);const a=node('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function handoff(id,token){show('handoff',true);$('client-url').value=location.origin+'/?client=1';$('share-id').value=id;$('share-key').value=token;}
async function list(){const rows=await api('/api/owner/requests');$('requests').replaceChildren();if(!rows.length)$('requests').append(ui('p','No requests yet. Start with one clear checklist.','hint'));for(const r of rows)$('requests').append(button(r.closed?'{0} · Closed':'{0}',async()=>{requestId=r.id;show('handoff',false);await load();},{0:r.title}));}
async function load(){current=await api(base());show('detail',true);show('owner-actions',role==='owner');$('request-title').textContent=current.title;I18n.text($('progress'),current.closed?'{0} of {1} approved · Request closed':'{0} of {1} approved',{0:current.items.filter(i=>i.state==='approved').length,1:current.items.length});I18n.text($('close'),current.closed?'Reopen request':'Close request');$('items').replaceChildren();
 for(const item of current.items){const card=node('article',undefined,'card');const top=node('div',undefined,'item-top');top.append(node('h3',item.label),ui('span',item.state.replaceAll('_',' '),'badge'));card.append(top);
 if(item.body)card.append(node('p',item.body,'answer'));
 if(item.attachment)card.append(button('Download {0}',()=>saveFile(`${base()}/items/${item.id}/files/${item.revision}`,item.attachment.filename),{0:item.attachment.filename}));
 card.append(ui('p','Revision {0}','hint',{0:item.revision}));
 for(const review of item.reviews){const line=node('p',undefined,'review');line.append(document.createTextNode(`v${review.revision} · `),ui('span',review.decision.replaceAll('_',' ')),document.createTextNode(review.note?' — '+review.note:''));card.append(line);}
 if(role==='client'&&!current.closed&&item.state!=='approved'){
  const form=node('form');const label=node('label');const input=node('textarea');input.rows=3;input.maxLength=20000;input.value=item.body;label.append(ui('span','Your response'),input);const fileLabel=node('label');const file=node('input');file.type='file';fileLabel.append(ui('span','Or attach a file (up to 10 MiB)'),file);const submit=ui('button','Submit response','primary');form.append(label,fileLabel,submit);form.onsubmit=e=>{e.preventDefault();action(async()=>{if(file.files.length){if(file.files[0].size>10*1024*1024)throw Error('File must be no larger than 10 MiB.');const data=new FormData();data.set('revision',item.revision);data.set('file',file.files[0]);await api(`${base()}/items/${item.id}/file`,{form:data});}else await api(`${base()}/items/${item.id}`,{data:{revision:item.revision,body:input.value}});await load();},submit);};card.append(form);
 }else if(role==='owner'&&item.revision){const label=node('label');const note=node('textarea');note.maxLength=2000;note.rows=2;label.append(ui('span','Review note'),note);const controls=node('div',undefined,'actions');for(const [title,decision] of [['Approve revision','approved'],['Request changes','changes_requested']]){const b=button(title,async()=>{await api(base()+'/review',{data:{item_id:item.id,revision:item.revision,decision,note:note.value}});await load();});if(decision==='approved'&&item.state==='approved')b.disabled=true;controls.append(b);}card.append(label,controls);}
 $('items').append(card);
 }
}
$('role').onchange=()=>show('request-field',$('role').value==='client');
if(new URLSearchParams(location.search).get('client')==='1'){$('role').value='client';show('request-field',true);}
$('login-form').onsubmit=e=>{e.preventDefault();action(async()=>{key=$('access-key').value;role=$('role').value;requestId=$('request-id').value.trim();if(role==='owner')await list();else{if(!requestId)throw Error('Enter the request ID.');await load();}show('login',false);show('welcome',false);show('workspace',true);show('owner-panel',role==='owner');show('logout',true);$('access-key').value='';},e.submitter);};
$('logout').onclick=()=>{key='';location.reload();};
$('create-form').onsubmit=e=>{e.preventDefault();action(async()=>{const result=await api('/api/owner/requests',{data:{title:$('title').value,labels:$('labels').value.split('\n').map(s=>s.trim()).filter(Boolean)}});requestId=result.id;handoff(result.id,result.token);await list();await load();$('create-form').reset();},e.submitter);};
$('close').onclick=()=>action(async()=>{await api(base()+'/closed',{data:{closed:!current.closed}});await load();await list();},$('close'));
$('rotate').onclick=()=>{if(confirm(I18n.t('Replace this client key? The previous key will stop working immediately.')))action(async()=>{const result=await api(base()+'/rotate',{data:{}});handoff(requestId,result.token);},$('rotate'));};
$('export').onclick=()=>action(()=>saveFile(base()+'/export','brief-history.json'),$('export'));
