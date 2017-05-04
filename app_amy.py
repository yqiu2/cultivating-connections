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
            return redirect(url_for('garden', uid=uid))
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
    session.pop('uid', None)
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
                    curs.execute('''
                        SELECT uid
                        FROM user_profile
                        where username = %s
                        ''', (username,))
                    result = curs.fetchall()
                    uid = result[0]['uid']
                    session['uid']= uid
                    return redirect(url_for('garden'))
                else:
                    flash("your passwords do not match")
                    return render_template("signup.html")
    else:
        print "sign up get"
    return render_template("signup.html")


# DISPLAY GARDEN 
@app.route('/garden/', methods=["GET", "POST"])
def garden():
    uid = session['uid']
    print 'uid', uid
    contacts = find_contacts(uid)
    garden_contents = display_contacts(contacts)
    return render_template("garden.html", garden=garden_contents)
    

# find_contacts finds all of your contacts
def find_contacts(uid):
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''SELECT 
        name, pid, cid, uid, photo, wateringFreq, droughtResist
        FROM contact_profile
        WHERE uid = %s
        ''', (uid,))
    results = curs.fetchall()

    for plant in results:
        state, url = find_state(plant)
        plant['state'] = state
        plant['url'] = url

    return results


# find_state returns the proper url of the image 
# matching your plant and your plant's state
def find_state(plant):
    # find the most recent interaction you've had with the person
    uid = plant['uid']
    pid = plant['pid']
    cid = plant['cid']
    curs = conn.cursor(MySQLdb.cursors.DictCursor)
    curs.execute('''SELECT 
        DATEDIFF(CURDATE(), MAX(interaction_log.date))as datediff
        FROM interaction_log 
        WHERE uid = %s
        AND cid =  %s
        ''', (uid, cid))
    results = curs.fetchall()

    # find the plant state
    state = 0 
    if len(results) > 0:
        datediff = results[0]['datediff']
        wateringFreq = plant['wateringFreq']
        droughtResist = plant['droughtResist']
        if datediff < wateringFreq:
            state = 1
        elif datediff < wateringFreq and datediff < wateringFreq+droughtResist:
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


# display contacts generates the html to display your garden
def display_contacts(contacts):
    NUM_COLS = 4
    res = ""
    res += "<table>\n"
    rowstarted = False
    for i, contact in enumerate(contacts):
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
            res += "<td>\n"+display_plant(contact)+"</td>\n"
            rowstarted = True
        else:
           res += "<td>\n"+display_plant(
                contact)+"</td>\n"

    res += "</table>\n"
    return res


# display plant generates the html that displays a plant 
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
    return res



if __name__ == '__main__':
    port = os.getuid()
    app.debug = True
    print('Running on port '+str(port))
    app.run('0.0.0.0',port)