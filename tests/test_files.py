import hashlib,json,tempfile,unittest
from unittest.mock import patch
from checklists import Checklists,RequestError

class FileTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=self.temp.name+'/db';self.store=Checklists(self.path);self.key,self.token=self.store.create('Brief',['Brand file']);self.item=self.store.view(self.key,self.token)['items'][0]['id']
 def tearDown(self):self.store.close();self.temp.cleanup()
 def upload(self,revision=0,name='brand.pdf',data=b'%PDF-test'):
  return self.store.submit_file(self.key,self.token,self.item,revision,name,data)
 def test_file_review_revision_and_export(self):
  self.upload();self.store.review(self.key,self.item,1,'changes_requested','New logo please')
  self.upload(1,data=b'new')
  with self.assertRaises(RequestError):self.store.review(self.key,self.item,1,'approved')
  self.assertEqual(self.store.download(self.key,self.token,self.item,1)['data'],b'%PDF-test')
  self.assertEqual(self.store.download(self.key,self.token,self.item,2)['data'],b'new')
  self.store.review(self.key,self.item,2,'approved')
  with self.assertRaises(RequestError):self.upload(2)
  history=json.loads(self.store.export(self.key,self.token))['items'][0]['history']
  self.assertEqual(history[1]['attachment']['sha256'],hashlib.sha256(b'new').hexdigest())
  self.assertNotIn('data',history[0]['attachment'])
 def test_download_isolation_and_revocation(self):
  self.upload();key,token=self.store.create('Other',['File'])
  with self.assertRaises(RequestError):self.store.download(key,token,self.item,1)
  new=self.store.rotate_token(self.key)
  with self.assertRaises(RequestError):self.store.download(self.key,self.token,self.item,1)
  self.assertEqual(self.store.download(self.key,new,self.item,1)['filename'],'brand.pdf')
 def test_unsafe_names_and_invalid_bytes(self):
  for name in ['../x','a/b','a\\b','.','..','x\r\ny','x\x00','x\u202ey','a'*201]:
   with self.assertRaises(RequestError):self.upload(name=name)
  for data in [b'',None,'text',b'x'*(10*1024*1024+1)]:
   with self.assertRaises(RequestError):self.upload(data=data)
  self.assertEqual(self.store.view(self.key,self.token)['items'][0]['revision'],0)
 def test_quota_failure_rolls_back_version(self):
  with patch('checklists.MAX_REQUEST_BYTES',10):
   self.upload(data=b'123456')
   with self.assertRaises(RequestError):self.upload(1,data=b'123456')
  self.assertEqual(self.store.view(self.key,self.token)['items'][0]['revision'],1)
  self.assertEqual(self.store.db.execute('SELECT count(*) FROM versions').fetchone()[0],1)
 def test_stale_and_closed_uploads(self):
  self.upload()
  with self.assertRaises(RequestError):self.upload()
  self.store.set_closed(self.key,True)
  with self.assertRaises(RequestError):self.upload(1)
 def test_text_and_files_can_replace_each_other(self):
  self.store.submit(self.key,self.token,self.item,0,'Text');self.upload(1)
  self.store.submit(self.key,self.token,self.item,2,'New text')
  self.assertIsNone(self.store.view(self.key,self.token)['items'][0]['attachment'])
  self.assertEqual(self.store.download(self.key,self.token,self.item,2)['data'],b'%PDF-test')
 def test_reopen_database_preserves_file(self):
  self.upload(name='品牌.pdf');self.store.close();self.store=Checklists(self.path)
  self.assertEqual(self.store.download(self.key,self.token,self.item,1)['filename'],'品牌.pdf')
