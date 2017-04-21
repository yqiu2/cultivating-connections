import MySQLdb
from dsn import DSN
import dbconn2
import jinja2
from flask import (Flask, render_template, make_response, request, redirect, url_for,
                   session, flash, send_from_directory)
from werkzeug import secure_filename
app = Flask(__name__)
import os
import imghdr

app.secret_key = 'cultivating conections is good for you.'

# ESTABLISHES CONNECTION TO MY DATABASE
DSN['db'] = 'yqiu2_db'
conn = dbconn2.connect(DSN)


# WATERING VIEW
@app.route('/addcontact/', methods=["GET", "POST"])
def add_contact():
	if request.method == 'GET':
		render_template('update.html')
	else:
		# process form



@app.route('/garden/', methods=["GET", "POST"])
def garden():
	curs = conn.cursor(MySQLdb.cursors.DictCursor)
        curs.execute('''SELECT person.name,  FROM contact_profile, interaction WHERE cid = ?;''', (cid))
        results = curs.fetchall()
	


if __name__ == '__main__':
    port = os.getuid()
    app.debug = True
    print('Running on port '+str(port))
    app.run('0.0.0.0',port)


