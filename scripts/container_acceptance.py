"""Disposable Docker persistence acceptance; never touches production volumes."""
import json,os,secrets,subprocess,tempfile,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
name='brief-test-'+secrets.token_hex(5);volume=name+'-data';restored=name+'-restore';key=secrets.token_urlsafe(32);image='brief-relay-acceptance:local'
def docker(*args):return subprocess.check_output(['docker',*args],text=True).strip()
def start(container,vol):
 docker('run','-d','--name',container,'--read-only','--tmpfs','/tmp:size=32m','--cap-drop=ALL','--security-opt=no-new-privileges:true','-e','BRIEF_OWNER_KEY='+key,'-v',vol+':/data','-p','127.0.0.1::8090',image)
 port=docker('port',container,'8090/tcp').rsplit(':',1)[1];base='http://127.0.0.1:'+port
 for _ in range(100):
  try:
   with urllib.request.urlopen(base,timeout=1) as r:
    if r.status==200:return base
  except (OSError,urllib.error.URLError):time.sleep(.1)
 raise RuntimeError('Server failed to start')
def call(base,path,token=key,data=None,raw=None,content_type=None):
 headers={'Authorization':'Bearer '+token}
 if data is not None:raw=json.dumps(data).encode();content_type='application/json'
 if content_type:headers['Content-Type']=content_type
 with urllib.request.urlopen(urllib.request.Request(base+path,data=raw,headers=headers),timeout=10) as r:return r.read()
try:
 base=start(name,volume)
 assert docker('exec',name,'id','-u')=='10001'
 result=json.loads(call(base,'/api/owner/requests',data={'title':'Persistence check','labels':['Logo']}));rid=result['id'];token=result['token'];url='/api/requests/'+rid
 item=json.loads(call(base,url,token))['items'][0]['id'];boundary='brief-test-boundary';payload=b'\x00verified attachment\xff'
 raw=(f'--{boundary}\r\nContent-Disposition: form-data; name="revision"\r\n\r\n0\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="logo.bin"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+payload+f'\r\n--{boundary}--\r\n'.encode())
 call(base,url+'/items/'+item+'/file',token,raw=raw,content_type='multipart/form-data; boundary='+boundary)
 call(base,'/api/owner/requests/'+rid+'/review',data={'item_id':item,'revision':1,'decision':'approved'})
 docker('restart',name)
 base='http://127.0.0.1:'+docker('port',name,'8090/tcp').rsplit(':',1)[1]
 # Wait for restarted process without creating another container.
 for _ in range(100):
  try:
   assert json.loads(call(base,url,token))['complete'];break
  except OSError:time.sleep(.1)
 else:raise RuntimeError('Restart failed')
 assert call(base,url+'/items/'+item+'/files/1',token)==payload
 docker('stop',name)
 with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
  source=Path(tmp)/'source.sqlite3';backup=Path(tmp)/'backup.sqlite3'
  docker('cp',name+':/data/brief.sqlite3',str(source))
  subprocess.run(['python3',str(ROOT/'scripts/backup.py'),str(source),str(backup)],check=True)
  assert backup.stat().st_mode & 0o777==0o600
  docker('volume','create',restored)
  docker('run','--rm','--user','0','-v',restored+':/data','-v',str(backup)+':/backup:ro',image,'python','-c',"import shutil,os;shutil.copyfile('/backup','/data/brief.sqlite3');os.chown('/data/brief.sqlite3',10001,10001);os.chmod('/data/brief.sqlite3',0o600);os.chown('/data',10001,10001)")
  restored_base=start(name+'-restored',restored)
  assert json.loads(call(restored_base,url,token))['complete']
  assert call(restored_base,url+'/items/'+item+'/files/1',token)==payload
  call(restored_base,'/api/owner/requests/'+rid+'/review',data={'item_id':item,'revision':1,'decision':'changes_requested','note':'After restore'})
  call(restored_base,url+'/items/'+item,token,data={'revision':1,'body':'Writes still work'})
  assert json.loads(call(restored_base,url,token))['items'][0]['revision']==2
 print('PASS: non-root container, file bytes, approval, restart persistence, private consistent backup, clean-volume restore and post-restore write')
finally:
 for container in (name,name+'-restored'):subprocess.run(['docker','rm','-f',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for vol in (volume,restored):subprocess.run(['docker','volume','rm',vol],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
