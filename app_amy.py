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
# session has username and uid
session['username'] = ''
session.pop('username', None)

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        return 'Logged in as ' + username + '<br>' + \
        "  <a href='/logout'> click here to log out</a></b>"
    return '''<p>You are not logged in </p> 
        <p><a href='/login'></b>
        click here to log in</b></a></p>
        <p><a href='/signup/'></b>
        click here to sign up</b></a></p>
        '''

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        uid = check_login(session, conn)
        if uid != None:
            session['uid'] = uid
            return render_template(url_for('garden', uid=uid))
        else:
            return redirect(url_for('login'))
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
    hash_pass = hashlib.sha256(session['password']).hexdigest()
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

@app.route('/signup/', methods = ['GET', 'POST'])
def signup():
    print '''in signup'''
    if request.method == 'POST':
        username = request.form['username'].strip()
        fname = request.form['fname'].strip()
        sname = request.form['sname'].strip()
        password1 = request.form['password1']
        password2 = request.form['password2']   
        if username != "":
            # you can add this username and password
            curs = conn.cursor(MySQLdb.cursors.DictCursor)
            curs.execute('''
                SELECT * 
                FROM user_profile
                WHERE username=%s
                ''', (username,))
            results = curs.fetchall()
            if len(results) > 0 :
                flash("This username is already taken"+ str(results))
                return render_template("signup.html")
            else:
                # unused username
                if password2 == password2:
                    # the user really intended this password!
                    hash_pass = hashlib.sha256(password1).hexdigest()
                    curs = conn.cursor(MySQLdb.cursors.DictCursor)
                    curs.execute('''
                        INSERT INTO user_profile 
                        ( firstName, lastName, password, hashpass, username) 
                        VALUES ( %s, %s, %s, %s, %s)
                        ''', (fname, sname, "", hash_pass, username))
                    print "added "+username+"to our system"
                    flash("welcome "+ username+ " to our app")

                    curs.execute('''
                        SELECT uid
                        FROM user_profile
                        where username = %s
                        ''', (username,))
                    result = curs.fetchall()
                    uid = result[0]['uid']
                    return render_template(url_for('garden', uid=uid))
                else:
                    flash("your passwords do not match")
                    return render_template("signup.html")
    else:
        print "sign up get"
    return render_template("signup.html")

# DISPLAY GARDEN 
@app.route('/garden/', methods=["GET", "POST"])
def garden(uid):
    username = session['username']
    contacts = find_contacts(uid)
    garden_contents = display_contacts(contacts)
    return render_template("garden", garden=garden_contents)
    
def find_contacts(uid):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''SELECT 
        name, pid, cid, uid, photo, wateringFreq, droughtResist
        FROM contact_profile
        AND uid = %s
        ''', (uid,))
    results = curs.fetchall()

    for plant in results:
        state, url = det_drought_state(plant)
        plant['state'] = state
        plant['url'] = url

    return results

# given a plant representing relationship between user and contact
# return a number (1-3) indicating the health of that relationship
# as well as the associated plant image url
def det_drought_state(plant):
    # find the most recent interaction you've had with the person
    uid = plant['uid']
    cid = plant['cid']
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''SELECT 
        MAX(date) as latest_date
        FROM interaction_log 
        WHERE uid = %s
        AND cid =  %s
        ''', (uid, cid))
    results = curs.fetchall()

    # find the plant state
    state = 0 
    if len(results) > 0:
        wateringFreq = plant['wateringFreq']
        droughtResist = plant['droughtResist']
        today = time.today()
        recent = today - results[latest_date]
        if recent < wateringFreq:
            state = 1
        elif recent < wateringFreq and recent < wateringFreq+droughtResist:
            state = 2
        else: 
            state = 3
    else:
        # no interactions recorded so far
        state = 1 
    plant['state'] = state

    # find plant url 
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''SELECT 
        image
        FROM plant_state 
        WHERE pid = %s
        AND state =  %s
        ''', (pid, state,))
    results = curs.fetchall()
    if len(results)> 0:
        url = results[0]['image']
    else:
        url = ""
    plant['url'] = url 
    return state, url


def display_contacts(contacts):
    NUM_COLS = 4
    res = ""
    res += "<table>\n"
    rowstarted = False
    for i, contact in contacts:
        if i == len(contacts):
            res += "<td>\n"+display_plant(
                contact)+"</td>\n"
            rowstarted = False
            res += "</tr>\n"
        elif i%NUM_COLS == 0 and rowstarted:
            res += "</tr>\n"
            res += "<tr>\n"
            res += "<td>\n"+display_plant(
                contact)+"</td>\n"
            rowstarted = True
        elif i%NUM_COLS == 0 and not rowstarted:
            res += "<tr>\n"
            res += "<td>\n"+display_plant(
                contact)+"</td>\n"
            rowstarted = True
        else:
           res += "<td>\n"+display_plant(
                contact)+"</td>\n"

    res += "</table>\n"

def display_plant(contact):
    res = ""
    res += "<img src="+contact['url']+" alt="+str(contact['name'])+">"
    res += "<br>"
    res += "<p>"+contact['name']+"</p>"
    # I would really want a progress bar
    if contact['state'] == 1:
        res += "<p>great</p>"
    elif contact['state'] == 2:
        res += "<p>water now</p>"
    else:
        res +="<p>your plant is dying</p>"


if __name__ == '__main__':
    port = os.getuid()
    app.debug = True
    print('Running on port '+str(port))
    app.run('0.0.0.0',port)


