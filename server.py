"""Local HTTP API. Owner bearer key is required; client keys are request-scoped."""
import hmac,io,os
from functools import wraps
from flask import Flask,g,jsonify,request,send_file
from werkzeug.exceptions import HTTPException
from checklists import Checklists,RequestError,MAX_FILE_BYTES


def create_app(database,owner_key):
    if not isinstance(owner_key,str) or len(owner_key)<32 or not owner_key.isascii():
        raise ValueError('BRIEF_OWNER_KEY must be at least 32 ASCII characters.')
    app=Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=MAX_FILE_BYTES+65536,MAX_FORM_MEMORY_SIZE=65536,MAX_FORM_PARTS=8)

    def store():
        if 'store' not in g:g.store=Checklists(database)
        return g.store

    def bearer():
        value=request.headers.get('Authorization','')
        return value[7:] if value.startswith('Bearer ') else ''

    def owner(fn):
        @wraps(fn)
        def protected(*args,**kwargs):
            if not hmac.compare_digest(bearer().encode(),owner_key.encode()):return jsonify(error='Owner access denied.'),401
            return fn(*args,**kwargs)
        return protected

    def body():
        value=request.get_json()
        if not isinstance(value,dict):raise RequestError('Expected a JSON object.')
        return value

    @app.teardown_appcontext
    def close(error):
        db=g.pop('store',None)
        if db:db.close()

    @app.after_request
    def headers(response):
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        return response

    @app.errorhandler(RequestError)
    def invalid(error):return jsonify(error=str(error)),400

    @app.errorhandler(HTTPException)
    def http_error(error):return jsonify(error=error.description),error.code

    @app.get('/')
    def workspace():return app.send_static_file('index.html')

    @app.get('/api/owner/requests')
    @owner
    def listing():
        return jsonify([dict(r) for r in store().db.execute('SELECT id,title,closed FROM requests ORDER BY rowid DESC')])

    @app.post('/api/owner/requests')
    @owner
    def create():
        b=body();key,token=store().create(b.get('title'),b.get('labels'))
        return jsonify(id=key,token=token),201

    @app.get('/api/owner/requests/<key>')
    @owner
    def owner_view(key):return jsonify(store().owner_view(key))

    @app.post('/api/owner/requests/<key>/review')
    @owner
    def review(key):
        b=body();store().review(key,b.get('item_id'),b.get('revision'),b.get('decision'),b.get('note',''))
        return jsonify(ok=True)

    @app.post('/api/owner/requests/<key>/rotate')
    @owner
    def rotate(key):return jsonify(token=store().rotate_token(key))

    @app.post('/api/owner/requests/<key>/closed')
    @owner
    def closed(key):store().set_closed(key,body().get('closed'));return jsonify(ok=True)

    @app.get('/api/owner/requests/<key>/export')
    @owner
    def export(key):
        return send_file(io.BytesIO(store().owner_export(key).encode()),mimetype='application/json',as_attachment=True,download_name='brief-history.json')

    @app.get('/api/requests/<key>')
    def client_view(key):return jsonify(store().view(key,bearer()))

    @app.post('/api/requests/<key>/items/<item>')
    def submit(key,item):
        store().authenticate(key,bearer())
        b=body();revision=store().submit(key,bearer(),item,b.get('revision'),b.get('body'))
        return jsonify(revision=revision),201

    @app.post('/api/requests/<key>/items/<item>/file')
    def upload(key,item):
        store().authenticate(key,bearer())
        file=request.files.get('file');revision=request.form.get('revision','')
        if file is None or not revision.isascii() or not revision.isdigit() or len(revision)>10:raise RequestError('File and numeric revision required.')
        result=store().submit_file(key,bearer(),item,int(revision),file.filename,file.stream.read(MAX_FILE_BYTES+1))
        return jsonify(revision=result),201

    def attachment(file):
        return send_file(io.BytesIO(file['data']),mimetype='application/octet-stream',as_attachment=True,download_name=file['filename'])

    @app.get('/api/requests/<key>/items/<item>/files/<int:revision>')
    def download(key,item,revision):return attachment(store().download(key,bearer(),item,revision))

    @app.get('/api/owner/requests/<key>/items/<item>/files/<int:revision>')
    @owner
    def owner_download(key,item,revision):return attachment(store().owner_download(key,item,revision))

    return app

if __name__=='__main__':
    os.umask(0o077)
    create_app(os.environ.get('BRIEF_DATABASE','brief.sqlite3'),os.environ.get('BRIEF_OWNER_KEY','')).run(host='127.0.0.1',port=8090,debug=False)
