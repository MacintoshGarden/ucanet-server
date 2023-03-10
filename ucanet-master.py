"""
Just testing stuff

gzip create from content:
with gzip.open('/home/joe/file.sql.gz', 'wb') as f:
    f.write(content)

gzip read content from gzipped file:
with gzip.open('/home/joe/file.sql.gz', 'rb') as f:
    file_content = f.read()
"""
import gzip
import sqlite3
from flask import Flask, g, send_file, request, jsonify

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(':memory:')
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('./server-db/master.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    response_body = {
        "hello": "world",
        "world": "hello"
    }
    return jsonify(response_body), 200

@app.route("/version")
def getversion():
    dbver = query_db('SELECT id FROM version', one=True)
    if dbver is None:
        print('Well, crap!')
    else:
        print(dbver['id'])

@app.route("/database/<path:fname>")
def download_file(fname):
    return send_from_directory(
        './server-db/', fname, as_attachment=True
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=8001)