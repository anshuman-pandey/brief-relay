"""Transactional checklist review core. Owner calls require an external auth layer."""
import hashlib,hmac,json,secrets,sqlite3,unicodedata
from datetime import datetime,timezone
MAX_FILE_BYTES=10*1024*1024
MAX_REQUEST_BYTES=100*1024*1024
class RequestError(ValueError):pass

def text(value,limit):
 if not isinstance(value,str) or not value.strip() or len(value)>limit or '\x00' in value:raise RequestError('Invalid or oversized text.')
 return value

def digest(token):return hashlib.sha256(token.encode()).hexdigest()

class Checklists:
 def __init__(self,path):
  self.db=sqlite3.connect(path,timeout=5);self.db.row_factory=sqlite3.Row;self.db.execute('PRAGMA foreign_keys=ON')
  self.db.executescript('''CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,title TEXT,token_hash TEXT,closed INTEGER DEFAULT 0);
  CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,request_id TEXT REFERENCES requests(id),label TEXT,revision INTEGER DEFAULT 0,state TEXT DEFAULT 'missing');
  CREATE TABLE IF NOT EXISTS versions(item_id TEXT REFERENCES items(id),revision INTEGER,body TEXT,created_at TEXT,PRIMARY KEY(item_id,revision));
  CREATE TABLE IF NOT EXISTS reviews(item_id TEXT,revision INTEGER,decision TEXT,note TEXT,created_at TEXT,FOREIGN KEY(item_id,revision) REFERENCES versions(item_id,revision));
  CREATE TABLE IF NOT EXISTS attachments(item_id TEXT,revision INTEGER,filename TEXT NOT NULL,data BLOB NOT NULL,sha256 TEXT NOT NULL,PRIMARY KEY(item_id,revision),FOREIGN KEY(item_id,revision) REFERENCES versions(item_id,revision));''')
 def close(self):self.db.close()
 def create(self,title,labels):
  text(title,200)
  if not isinstance(labels,list) or not 1<=len(labels)<=50:raise RequestError('Use 1 to 50 checklist items.')
  labels=[text(label,500) for label in labels];key=secrets.token_urlsafe(16);token=secrets.token_urlsafe(32)
  with self.db:
   self.db.execute('INSERT INTO requests(id,title,token_hash) VALUES(?,?,?)',(key,title,digest(token)))
   for label in labels:self.db.execute('INSERT INTO items(id,request_id,label) VALUES(?,?,?)',(secrets.token_urlsafe(16),key,label))
  return key,token
 def authenticate(self,key,token):
  row=self.db.execute('SELECT * FROM requests WHERE id=?',(key,)).fetchone()
  if row is None or not isinstance(token,str) or not hmac.compare_digest(row['token_hash'],digest(token)):raise RequestError('Request access denied.')
  return row
 def view(self,key,token):
  self.authenticate(key,token)
  return self.owner_view(key)
 def owner_view(self,key):
  row=self.db.execute("SELECT * FROM requests WHERE id=?",(key,)).fetchone()
  if row is None:raise RequestError("Request not found.")
  items=[]
  for item in self.db.execute('SELECT * FROM items WHERE request_id=? ORDER BY rowid',(key,)):
   version=self.db.execute('SELECT body FROM versions WHERE item_id=? AND revision=?',(item['id'],item['revision'])).fetchone()
   notes=[dict(n) for n in self.db.execute('SELECT revision,decision,note,created_at FROM reviews WHERE item_id=? ORDER BY rowid',(item['id'],))]
   items.append(dict(id=item['id'],label=item['label'],revision=item['revision'],state=item['state'],body=version['body'] if version else '',reviews=notes,attachment=self._metadata(item['id'],item['revision'])))
  return dict(id=key,title=row['title'],closed=bool(row['closed']),items=items,complete=all(i['state']=='approved' for i in items))
 def submit(self,key,token,item_id,expected_revision,body):
  return self._submit(key,token,item_id,expected_revision,text(body,20000))
 def submit_file(self,key,token,item_id,expected_revision,filename,data):
  text(filename,200)
  if filename in ('.','..') or any(c in filename for c in '/\\') or any(unicodedata.category(c).startswith('C') for c in filename):raise RequestError('Use a plain filename without paths or control characters.')
  if type(data) is not bytes or not 1<=len(data)<=MAX_FILE_BYTES:raise RequestError('File must contain 1 byte to 10 MiB.')
  return self._submit(key,token,item_id,expected_revision,'',(filename,data))
 def _metadata(self,item_id,revision):
  row=self.db.execute('SELECT filename,length(data) AS size,sha256 FROM attachments WHERE item_id=? AND revision=?',(item_id,revision)).fetchone()
  return dict(row) if row else None
 def download(self,key,token,item_id,revision):
  self.authenticate(key,token)
  return self.owner_download(key,item_id,revision)
 def owner_download(self,key,item_id,revision):
  if type(revision) is not int or revision<1:raise RequestError('Invalid revision.')
  row=self.db.execute('SELECT a.filename,a.data,a.sha256 FROM attachments a JOIN items i ON i.id=a.item_id WHERE i.request_id=? AND a.item_id=? AND a.revision=?',(key,item_id,revision)).fetchone()
  if row is None:raise RequestError('Attachment not found.')
  return dict(row)
 def _submit(self,key,token,item_id,expected_revision,body,attachment=None):
  if type(expected_revision) is not int or expected_revision<0:raise RequestError('Invalid revision.')
  with self.db:
   self.db.execute('BEGIN IMMEDIATE');request=self.authenticate(key,token)
   if request['closed']:raise RequestError('Request is closed.')
   item=self.db.execute('SELECT * FROM items WHERE id=? AND request_id=?',(item_id,key)).fetchone()
   if item is None:raise RequestError('Item not found.')
   if item['revision']!=expected_revision:raise RequestError('Item changed. Reload before submitting.')
   if item['state']=='approved':raise RequestError('Approved items must be reopened by the owner.')
   revision=expected_revision+1
   self.db.execute('INSERT INTO versions VALUES(?,?,?,?)',(item_id,revision,body,datetime.now(timezone.utc).isoformat()))
   if attachment:
    filename,data=attachment
    used=self.db.execute('SELECT COALESCE(sum(length(a.data)),0) FROM attachments a JOIN items i ON i.id=a.item_id WHERE i.request_id=?',(key,)).fetchone()[0]
    if used+len(data)>MAX_REQUEST_BYTES:raise RequestError('Request attachment storage limit reached (100 MiB including history).')
    self.db.execute('INSERT INTO attachments VALUES(?,?,?,?,?)',(item_id,revision,filename,data,hashlib.sha256(data).hexdigest()))
   self.db.execute("UPDATE items SET revision=?,state='submitted' WHERE id=?",(revision,item_id))
  return revision
 def review(self,key,item_id,revision,decision,note=''):
  text(item_id,100)
  if decision not in ('approved','changes_requested'):raise RequestError('Invalid decision.')
  if decision=='changes_requested':text(note,2000)
  elif not isinstance(note,str) or len(note)>2000:raise RequestError('Invalid review note.')
  if type(revision) is not int or revision<1:raise RequestError('Invalid revision.')
  with self.db:
   self.db.execute('BEGIN IMMEDIATE')
   item=self.db.execute('SELECT * FROM items WHERE id=? AND request_id=?',(item_id,key)).fetchone()
   if item is None or item['revision']!=revision:raise RequestError('Review refers to an outdated item.')
   if item['state']=='missing':raise RequestError('No response to review.')
   self.db.execute('INSERT INTO reviews VALUES(?,?,?,?,?)',(item_id,revision,decision,note,datetime.now(timezone.utc).isoformat()))
   self.db.execute('UPDATE items SET state=? WHERE id=?',(decision,item_id))
 def rotate_token(self,key):
  token=secrets.token_urlsafe(32)
  with self.db:
   if not self.db.execute('UPDATE requests SET token_hash=? WHERE id=?',(digest(token),key)).rowcount:raise RequestError('Request not found.')
  return token
 def set_closed(self,key,closed):
  if type(closed) is not bool:raise RequestError('Closed must be boolean.')
  with self.db:
   if not self.db.execute('UPDATE requests SET closed=? WHERE id=?',(int(closed),key)).rowcount:raise RequestError('Request not found.')
 def export(self,key,token):
  self.authenticate(key,token)
  return self.owner_export(key)
 def owner_export(self,key):
  result=self.owner_view(key)
  for item in result['items']:
   item['history']=[dict(r) for r in self.db.execute('SELECT revision,body,created_at FROM versions WHERE item_id=? ORDER BY revision',(item['id'],))]
   for version in item['history']:version['attachment']=self._metadata(item['id'],version['revision'])
  return json.dumps(result,ensure_ascii=False,indent=2)
