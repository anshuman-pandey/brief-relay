import json,tempfile,unittest
from checklists import Checklists,RequestError
class ReviewTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=self.temp.name+'/db';self.store=Checklists(self.path);self.key,self.token=self.store.create('Website brief',['Describe your audience','Describe your goals']);self.item=self.store.view(self.key,self.token)['items'][0]['id']
 def tearDown(self):self.store.close();self.temp.cleanup()
 def test_revision_review_cycle(self):
  self.store.submit(self.key,self.token,self.item,0,'First draft');self.store.review(self.key,self.item,1,'changes_requested','Please be more specific');self.store.submit(self.key,self.token,self.item,1,'Second draft');self.store.review(self.key,self.item,2,'approved')
  row=self.store.view(self.key,self.token)['items'][0];self.assertEqual(row['state'],'approved');self.assertEqual(len(row['reviews']),2);self.assertFalse(self.store.view(self.key,self.token)['complete'])
 def test_stale_review_cannot_approve_new_answer(self):
  self.store.submit(self.key,self.token,self.item,0,'One');self.store.submit(self.key,self.token,self.item,1,'Two')
  with self.assertRaises(RequestError):self.store.review(self.key,self.item,1,'approved')
  self.assertEqual(self.store.view(self.key,self.token)['items'][0]['state'],'submitted')
 def test_stale_client_cannot_overwrite(self):
  self.store.submit(self.key,self.token,self.item,0,'One')
  with self.assertRaises(RequestError):self.store.submit(self.key,self.token,self.item,0,'Two')
 def test_approval_locks_until_owner_requests_change(self):
  self.store.submit(self.key,self.token,self.item,0,'One');self.store.review(self.key,self.item,1,'approved')
  with self.assertRaises(RequestError):self.store.submit(self.key,self.token,self.item,1,'Two')
  self.store.review(self.key,self.item,1,'changes_requested','Update this');self.store.submit(self.key,self.token,self.item,1,'Two')
 def test_token_rotation_revokes_old_access(self):
  new=self.store.rotate_token(self.key)
  with self.assertRaises(RequestError):self.store.view(self.key,self.token)
  self.assertEqual(self.store.view(self.key,new)['title'],'Website brief')
 def test_closed_request_rejects_submit(self):
  self.store.set_closed(self.key,True)
  with self.assertRaises(RequestError):self.store.submit(self.key,self.token,self.item,0,'One')
 def test_cross_request_item_rejected(self):
  key,token=self.store.create('Other',['Other item'])
  with self.assertRaises(RequestError):self.store.submit(key,token,self.item,0,'One')
  with self.assertRaises(RequestError):self.store.review(key,self.item,1,'approved')
 def test_export_preserves_history_without_credentials(self):
  self.store.submit(self.key,self.token,self.item,0,'One');self.store.submit(self.key,self.token,self.item,1,'Two');raw=self.store.export(self.key,self.token);self.assertNotIn(self.token,raw);self.assertNotIn('token_hash',raw);self.assertEqual(len(json.loads(raw)['items'][0]['history']),2)
 def test_invalid_input_rolls_back(self):
  for body in ['',None,'a'*20001]:
   with self.assertRaises(RequestError):self.store.submit(self.key,self.token,self.item,0,body)
  self.assertEqual(self.store.view(self.key,self.token)['items'][0]['revision'],0)
 def test_persistence(self):
  self.store.submit(self.key,self.token,self.item,0,'Saved');self.store.close();self.store=Checklists(self.path);self.assertEqual(self.store.view(self.key,self.token)['items'][0]['body'],'Saved')
