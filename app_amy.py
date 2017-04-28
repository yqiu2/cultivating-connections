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
from datetime import date

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


# DISPLAY GARDEN 
@app.route('/garden/', methods=["GET", "POST"])
def garden():
    #  PLEASE IMPLEMENT <username>/garden to distinguish between different users
    username = "vngan"
	contacts = findcontacts(username)
	
def find_contacts(username):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''SELECT 
        name, pid, cid, uid, photo, wateringFreq, droughtResist
        FROM contact_profile, user_profile, 
        WHERE user_profile.username = %s
        AND user_profile.uid =  contact_profile.uid
        ''', (username))
    results = curs.fetchall()
    return results

# given a relationship and relationship wateringFrequency and droughtResist
# return a number (1-3) indicating the health of that relationship
def det_drought_state(wateringFreq, droughtResist, uid, cid):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''SELECT 
        MAX(date) as latest_date
        FROM interaction_log 
        WHERE uid = %s
        AND cid =  %s
        ''', (uid, cid))
    results = curs.fetchall()
    today = time.today()
    recent = today - results[latest_date]
    if recent < wateringFreq:
        return 1
    elif recent < wateringFreq and r

if __name__ == '__main__':
    port = os.getuid()
    app.debug = True
    print('Running on port '+str(port))
    app.run('0.0.0.0',port)


