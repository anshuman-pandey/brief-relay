import io,json,tempfile,unittest
from server import create_app
class HTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.app=create_app(self.tmp.name+'/db','o'*40);self.c=self.app.test_client();self.owner={'Authorization':'Bearer '+'o'*40}
  self.created=self.c.post('/api/owner/requests',headers=self.owner,json={'title':'Website brief','labels':['Brand assets']}).get_json();self.key=self.created['id'];self.client={'Authorization':'Bearer '+self.created['token']};self.url='/api/requests/'+self.key;self.own='/api/owner/requests/'+self.key
  self.item=self.c.get(self.url,headers=self.client).get_json()['items'][0]['id'];self.itemurl=self.url+'/items/'+self.item
 def tearDown(self):self.tmp.cleanup()
 def upload(self,revision=0,data=b'<script>alert(1)</script>'):
  return self.c.post(self.itemurl+'/file',headers=self.client,data={'revision':str(revision),'file':(io.BytesIO(data),'brand.html')})
 def test_end_to_end_file_revision_approval(self):
  self.assertEqual(self.upload().status_code,201)
  review={'item_id':self.item,'revision':1,'decision':'changes_requested','note':'Send a PDF'}
  self.assertEqual(self.c.post(self.own+'/review',headers=self.owner,json=review).status_code,200)
  self.assertEqual(self.upload(1,b'%PDF example').status_code,201)
  review.update(revision=2,decision='approved')
  self.assertEqual(self.c.post(self.own+'/review',headers=self.owner,json=review).status_code,200)
  self.assertTrue(self.c.get(self.url,headers=self.client).get_json()['complete'])
  self.assertEqual(self.upload(2).status_code,400)
  exported=self.c.get(self.own+'/export',headers=self.owner)
  self.assertEqual(len(json.loads(exported.data)['items'][0]['history']),2)
 def test_owner_routes_reject_client_and_missing_key(self):
  for headers in [{},self.client]:
   self.assertEqual(self.c.get('/api/owner/requests',headers=headers).status_code,401)
   self.assertEqual(self.c.post(self.own+'/review',headers=headers,json={}).status_code,401)
   self.assertEqual(self.c.post(self.own+'/rotate',headers=headers).status_code,401)
   self.assertEqual(self.c.get(self.own+'/export',headers=headers).status_code,401)
 def test_attachment_headers_and_revocation(self):
  self.upload();url=self.itemurl+'/files/1';r=self.c.get(url,headers=self.client)
  self.assertEqual(r.mimetype,'application/octet-stream');self.assertTrue(r.headers['Content-Disposition'].startswith('attachment;'));self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff');self.assertEqual(r.headers['Cache-Control'],'no-store')
  self.c.post(self.own+'/rotate',headers=self.owner)
  self.assertEqual(self.c.get(url,headers=self.client).status_code,400)
  self.assertEqual(self.c.get(self.own+'/items/'+self.item+'/files/1',headers=self.owner).status_code,200)
 def test_body_limit_no_partial_write(self):
  self.app.config['MAX_CONTENT_LENGTH']=100
  self.assertEqual(self.upload(data=b'x'*101).status_code,413)
  self.assertEqual(self.c.get(self.url,headers=self.client).get_json()['items'][0]['revision'],0)
 def test_closed_and_bad_json_errors(self):
  self.assertEqual(self.c.post(self.itemurl,headers=self.client,json=[]).status_code,400)
  self.assertEqual(self.c.post(self.itemurl,headers=self.client,data='bad',content_type='application/json').status_code,400)
  self.c.post(self.own+'/closed',headers=self.owner,json={'closed':True})
  self.assertEqual(self.upload().status_code,400)
 def test_no_cors_or_cookie_auth(self):
  r=self.c.get('/api/owner/requests',headers={'Origin':'https://evil.example','Cookie':'owner='+'o'*40})
  self.assertEqual(r.status_code,401);self.assertNotIn('Access-Control-Allow-Origin',r.headers)
 def test_malformed_review_item_returns_json_error(self):
  r=self.c.post(self.own+'/review',headers=self.owner,json={'item_id':{},'revision':1,'decision':'approved'})
  self.assertEqual(r.status_code,400);self.assertIn('error',r.get_json())
 def test_owner_key_required(self):
  with self.assertRaises(ValueError):create_app(self.tmp.name+'/other','short')
