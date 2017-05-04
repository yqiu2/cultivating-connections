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
import hashlib
from datetime import date

app.secret_key = 'cultivating connections is good for you.'

# ESTABLISHES CONNECTION TO MY DATABASE
DSN['db'] = 'yqiu2_db'
conn = dbconn2.connect(DSN)


session = {}
session['username'] = 'admin'
session.pop('username', None)

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']


        return 'Logged in as ' + username + '<br>' + \
        "  <a href='/logout'> click here to log out</a></b>"
    return "<p>You are not logged in </p> <p><a href='/login'></b>" + \
        "click here to log in</b></a></p>"

@app.route('/login/', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        uid = check_login(session, conn)
        return redirect(url_for('index'))
    return '''
    <form action="" method="POST">
        <label><b>Username</b></label>
        <input type="text" placeholder="Enter Username" name="username" required>
        <label><b>Password</b></label>
        <input type="password" placeholder="Enter Password" name="password" required>
        <p><input type=submit value=Login></p>
    </form>

    '''
@app.route('/logout/')
def logout():
    # remove the username from the session if it is there
    session.pop('username', None)
    return redirect(url_for('index'))

def check_login(session, conn):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    username = session['username']
    hash_pass = hashlib.sha256(session['password'])
    print 'hashpass', str(hash_pass)
    curs.execute('''SELECT 
        uid, hashpass
        FROM user_profile 
        WHERE user_profile.username = %s
        AND user_profile.hashpass =  %s
        ''', (username,hash_pass,))
    results = curs.fetchall()
    print 'results', results
    if len(results)> 0 :
        print "there was a match!"
        return results[0]['uid']
    else:
        return None

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password1 = request.form['password1']
        password2 = request.form['password2']   
        if username.strip != "":
            # you can add this username and password
            curs = conn.cursor(MySQLdb.cursors.DictCursor)
            curs.execute('''
                SELECT * 
                FROM user_profile
                WHERE username = %s
                ''')
            if len(curs.fetchall()) > 0 :
                flash("This username is already taken")
                render_template("signup.html")
            else:
                # unused username
                if password2 == password2:
                    # the user really intended this password!
                    curs = conn.cursor(MySQLdb.cursors.DictCursor)
                    curs.execute('''
                        ISERT * 
                        FROM user_profile
                        WHERE username = %s
                        ''')
                else:


# DISPLAY GARDEN 
@app.route('/garden/', methods=["GET", "POST"])
def garden(uid):
    username = "vngan"
    contacts = find_contacts(uid)
    display_contacts(contacts)
    
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
    elif recent < wateringFreq and recent < wateringFreq+droughtResist:
        return 2
    else: 
        return 3

def display_contacts(contacts):


if __name__ == '__main__':
    port = os.getuid()
    app.debug = True
    print('Running on port '+str(port))
    app.run('0.0.0.0',port)


