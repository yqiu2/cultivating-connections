#!/usr/local/bin/python2.7

# Vicki Ngan
# CS 304 Cultivating Connections

# THINGS LEFT TO DO:
# DECIDE ON WHETHER OR NOT WE WANT TO ALLOW THEM TO UPDATE PLANT ID 
# CACHE DILEMMA -- FIX NEXT ROUND, REFRESHING PAGE AFTER SUBMITTING A NEW PHOTO DOESN'T DISPLAY NEW IMAGE (MUST OPEN ANOTHER BROWSER TO SEE NEW PHOTO)
# CONSIDER ORDER OF INTERACTIONS DISPLAYED IN INTERACTIONS LOG
# COOKIES -- MUST BE ABLE TO SAVE UID AND CID SO THAT WE CAN ADD NEW INTERACTIONS/VIEW CONTACT WITHOUT ALLOWING OTHER USERS TO DO THE SAME

# IMPORT NECESSARY LIBRARIES AND FILES
import MySQLdb
from vngan_dsn import DSN
import dbconn2
import jinja2
from flask import (Flask, render_template, make_response, request, redirect, url_for,
                   session, flash, send_from_directory)
from werkzeug import secure_filename
app = Flask(__name__)
import os
import imghdr

app.secret_key = 'final project assignment'

# ESTABLISHES CONNECTION TO MY DATABASE
DSN['db'] = 'vngan_db'
conn = dbconn2.connect(DSN)


# WATERING VIEW
@app.route('/add/<uid>', methods=["GET", "POST"]) # DO NOT want to allow users ability to change other people's interactions! (CHANGE THIS)
def add(uid): # CANNOT PASS IN UID THROUGH URL -- it's dangerous! (cookies?)
	contacts = getContacts(uid)
	if contacts == None: 
		return render_template('error.html')
	if request.method == 'GET':
		return render_template('addInteraction.html', contacts = contacts)
	if request.method == 'POST':
		cid = request.form['menu-cid']
		quality = request.form['menu-quality']
		notes = request.form['notes']
		date = request.form['date'] # THINK ABOUT HOW USER WILL ENTER DATE

		# CHECK FIELDS
		if not notes.strip(): 
			notes = None
		if not date.strip(): 
			date = None 
		if quality == 0: 
			quality == None

		interaction = [cid, uid, date, quality, notes]
		contactFirstName = getContactInfo(cid)['firstName'] # consider better method

		try:
			insertInteraction(interaction)
			flash("Hooray, you added an interaction for " + contactFirstName + "!")
		except Exception as err:
			print "An error occurred: ", err
			flash("THERE IS SOMETHING WRONG WITH INSERT") # debugging purposes
			return render_template('addInteraction.html', contacts = contacts)

		return render_template('addInteraction.html', contacts = contacts)


# PLANT VIEW
# SAME AS UID --- THERE ARE ISSUES IF WE PUT THE CID IN THE LINK, CAUSE THEN OTHER USERS MAY ENTER :(
@app.route('/contact/<cid>', methods=["GET", "POST"])
def contact(cid):
	contact_info = getContactInfo(cid)
	if contact_info == None:
		return render_template('error.html') # change this later
	contact_info['plantPhoto'] = getPlantPhoto(contact_info['pid'])
	interactions = getInteractions(cid)
	if request.method == 'GET':
		return render_template('plantView.html', contact_info = contact_info, interactions = interactions)
	if request.method == 'POST': 
		try: 
			# reading user edits
			f = request.files['file']
			# CACHE PROBLEM!!! (doesn't renew images)
			mime_type = imghdr.what(f.stream)
			if mime_type != 'jpeg':
				raise Exception('Not a JPEG')
			filename = secure_filename(str(contact_info['cid'])+'.jpeg')
			pathname = 'static/'+filename
			contact_info['photo'] = filename
			f.save(pathname)
			flash('Upload successful')

			# updating database 
			contact_info_list = [contact_info['wateringFreq'],contact_info['droughtResist'],contact_info['firstName'],
			contact_info['lastName'], contact_info['photo'], contact_info['birthday'], contact_info['notes'], 
			contact_info['address'], contact_info['phnum'], contact_info['cid']]
			updateContactProfile(contact_info_list)
			
			return render_template('plantView.html', contact_info = contact_info, interactions = interactions)
		except Exception as err:
			flash('Upload failed {why}'.format(why=err))
			return render_template('plantView.html', contact_info = contact_info, interactions = interactions)

# getPlantPhoto(pid) returns the image path of a plant
def getPlantPhoto(pid): 
	curs = conn.cursor(MySQLdb.cursors.DictCursor)
	curs.execute('''SELECT image FROM plant WHERE pid = {pid};'''.format(pid = pid))
	results = curs.fetchall()
	return results[0]['image']

# should we allow them to update the plant (pid)?
# updateContactProfile(contact_info) updates information about a contact
def updateContactProfile(contact_info): 
	curs = conn.cursor()
	curs.execute('''UPDATE contact_profile SET wateringFreq = %s, droughtResist = %s, firstName = %s, lastName = %s, photo = %s,
		birthday = %s, notes = %s, address = %s, phnum = %s WHERE cid = %s;''', contact_info)


# insert interactions allows user to insert a new interaction into the interaction log
def insertInteraction(interaction): 
	curs = conn.cursor()
	curs.execute('''INSERT INTO interaction_log (cid, uid, date, quality, notes)  VALUES (%s,%s,%s,%s,%s);''', interaction)


# getContactInfo(cid) returns a dictionary of all of the information about ONE contact (by cid)
def getContactInfo(cid): 
	curs = conn.cursor(MySQLdb.cursors.DictCursor)
	curs.execute('''SELECT * FROM contact_profile WHERE cid = {cid};'''.format(cid = cid))
	results = curs.fetchall()
	if len(results) == 0: 
		return None 
	else: 
		return results[0]

# getContacts(uid) returns the cids and names of all of the user's contacts (by uid)
def getContacts(uid): 
	curs = conn.cursor(MySQLdb.cursors.DictCursor)
	curs.execute('''SELECT cid, firstName, lastName FROM contact_profile WHERE uid = {uid};'''.format(uid = uid))
	results = curs.fetchall()
	if len(results) == 0: 
		return None 
	contacts = {}
	for result in results: 
		full_name = getFullName(result)
		contacts[result['cid']] = full_name
	return contacts

# getFullName(result) takes a dictionary and returns a "full name" by concatenating the first and last name
def getFullName(result):
	full_name_template = full_name_template = "{firstName} {lastName}"
	full_name = full_name_template.format(firstName = result['firstName'], lastName = result['lastName'])
	return full_name

# getInteractions(cid) gets the dates and notes from the interaction log (database) by cid
def getInteractions(cid): 
	curs = conn.cursor(MySQLdb.cursors.DictCursor)
	curs.execute('''SELECT date, notes FROM interaction_log WHERE cid = {cid};'''.format(cid = cid))
	results = curs.fetchall()
	if len(results) == 0: 
		interactions['NO ENTRY'] = 'DOES NOT EXIST' 
		return interactions
	else: 
		interactions = []
		for result in results:
			interactions.append((result['date'], result['notes']))
		return interactions


if __name__ == '__main__':
    port = os.getuid()
    app.debug = True
    print('Running on port '+str(port))
    app.run('0.0.0.0',port)
