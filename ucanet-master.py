"""
wip
"""
import gzip
import sqlite3
import configparser
from flask import Flask, send_file, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
	response_body = {
		"hello": "world",
		"world": "hello"
	}
	return jsonify(response_body), 200

def validate_apikey(api_key):
	valid_key = "hardcorehardcode"
	if valid_key == api_key:
		return True

@app.route("/test")
def testapi():
	key = request.headers.get('X-API-Key')
	if validate_apikey(key):
		print('Valid: %s'%key)
		return '%s is a valid key, thanksyou'%key
	else:
		print('Invalid or no key supplied!')
		return 'Invalid keEEEEEEyY!'

@app.route("/sql/dump")
def dumpcurrent():
	data = ""
	con = sqlite3.connect('ucanet-registry.db')

	cursor.execute('SELECT rowid FROM revision')
	rev = cursor.fetchone()

	for line in con.iterdump():
		data += '%s\n' % line

	with gzip.open('archive/ucanet-registry-r%s.sql.gz'%str(data[0]), 'wt') as f:
		f.write(data)

	return('Work Complete!')

@app.route("/revision")
def getversion():
	connect = sqlite3.connect('ucanet-registry.db')
	cursor = connect.cursor()
	cursor.execute('SELECT rowid FROM revision')

	data = cursor.fetchone()
	return str(data[0])

@app.route("/database/<path:fname>")
def download_file(fname):
    return send_from_directory(
        './archive/', fname, as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8001)
