from flask import Flask, render_template, session,request, json, url_for, redirect
from flask import send_from_directory
from dotenv import load_dotenv
import pymysql
import hashlib
import os
from keras.models import load_model
from tensorflow.keras.utils import load_img # type: ignore
import numpy as np
import tensorflow as tf
from datetime import datetime
import json # For Redis
import redis # For Redis

load_dotenv()
emm=os.getenv('ADMIN_EMAIL')
databaseHost=os.getenv('databaseHost')
databaseUser=os.getenv('databaseUser')
databasePass=os.getenv('databasePass')
cacheHost=os.getenv('cacheHost')
cachePort=os.getenv('cachePort')
appSecretKey=os.getenv('appSecretKey')
redisCache = redis.StrictRedis(host=cacheHost, port=cachePort, db=0)
db = pymysql.connect(host=databaseHost,
                             user=databaseUser,
                             password=databasePass,
                             database='mushroom',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

dir_path = os.path.dirname(os.path.realpath(__file__))
staticURL=dir_path+'/static'
UPLOAD_FOLDER = dir_path + '/uploads'
model = load_model(staticURL + '/' + 'firstModel')



app = Flask(__name__)


app.secret_key = appSecretKey


@app.route("/")
def home():
	if session:
		return render_template('home.html')
	else:
		return render_template('index.html')
		
@app.route('/secure-login', methods=['POST'])
def signin():
	#adding a key to secure form against injection
	#can further encrypt this key
	form_secure = 'This$#is#$my#$Secret@#Key!@#'
	bmbm=os.getenv('mm')
	print('Agha negah kon', bmbm)
	form_key = request.form['form_secure']
	#check if form security key is present
	if form_key and form_key==form_secure:
		#collect login-form inputs
		username = request.form['username']
		password = request.form['password']
		h = hashlib.md5(password.encode())
		password = h.hexdigest()
		#user_group from database
		if request.method == 'POST' and username  and password:
			# Check if account exists using MySQL
			cursor = db.cursor()
			sql = 'SELECT * FROM accounts WHERE username = %s'
			cursor.execute(sql, username)
			# Fetch one record and return result
			account = cursor.fetchone()
			# If account exists in accounts table in our database
			if account and (password) == account['password']:
				session['signin'] = True
				session['username'] = username
				session['sessionkey'] = password
				return render_template('home.html')
			else:
				msg = "Credentians is not valid!"
				return render_template('index.html', msg=msg)
		else:
			msg = "Something went 3!"
			return render_template('index.html', msg=msg)
	else:
		msg = "Something went wrong 4!"
		return render_template('index.html', msg=msg)



def predictML(full_path):
    data = load_img(full_path, target_size=(256, 256, 3))
    data = np.expand_dims(data, axis=0)
    data = data * 1.0 / 255

#    with graph.as_default():
    p = model.predict(data)
    j=p.copy()
    accuracyPercentage=max(j[0][0],j[0][1])
    for i,val in enumerate(p):
        if val[0]<=0.3:
            val[0]=1
        else:
            val[0]=0

        if val[1]<=0.3:
            val[1]=1
        else:
            val[1]=0
    if p[0][0]==0:
        predictionResult= 'non_poisonous'
    else:
        predictionResult='poisonous'
    
    return (predictionResult, accuracyPercentage)





@app.route('/logout')
def logout():
	session.pop('signin', None)
	session.pop('username', None)
	session.pop('sessionkey', None)
	return redirect(url_for('home'))
		
@app.route('/signup')
def signup():
	return render_template('signup.html')


@app.route('/register',  methods=['POST', 'GET'])
def register():
	#adding a key to secure form against injection
	#can further encrypt this key
	form_secure = 'This$#is#$my#$Secret@#Key!@#' 
	form_key = request.form['form_secure']
	#check if form security key is present
	if form_key and form_key==form_secure:
		username = request.form['username']
		password = request.form['password']
		#encode our user submitted password
		h = hashlib.md5(password.encode())
		password = h.hexdigest()

		email = request.form['email']
		#check that all fields have been submitted
		if request.method == 'POST' and username and password and email:
			
			# Check if account exists using MySQL
			cursor = db.cursor()
			sql = 'SELECT * FROM accounts WHERE username = %s'
			cursor.execute(sql, username)
			# Fetch one record and return result
			account = cursor.fetchone()
			# If account exists in accounts table in out database
			if account:
				msg = 'Error! User account or email already exists!'
				return render_template('signup.html', msg=msg)
			else:
				cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)',(username, password, email))
				# the connection is not autocommited by default. So we must commit to save our changes.
				db.commit()
				msg = 'successfully registered!<a href="/"> Continue to Login..</a>'
				return username + ' ' + msg
		else:
			msg = 'something went wrong'
			return render_template('signup.html', msg = msg)

		#return 'successfully regestered user: '+ username
	else:
		msg = 'something went wrong'
		return render_template('signup.html', msg = msg)
		

@app.route('/profile')
def profile():
	username = session['username']
	sessionkey = session['sessionkey']
	# Check if account exists using MySQL
	cursor = db.cursor()
	sql = 'SELECT * FROM accounts WHERE username = %s'
	cursor.execute(sql, username)
	# Fetch one record and return result
	account = cursor.fetchone()
			# If account exists in accounts table in out database
	if account and (sessionkey == account['password']):
		#return 'Your personal details:<br>Username: ' + account[1] + '<br>' + 'Email: '+ account[3] + '<br>Password: ' + account[2] + '<br>(session pwd: '+ password +')'
		return render_template('profile.html', userid = account['id'], username = account['username'],ID = account['id'],email = account['email'])
		
	else:
		return 'No matching record found!'
	
		

@app.route('/last_check')
def lastCheck():
    
    userName=str(session['username'])        
    try:
        a1 = datetime.now()
        unpacked_check_result = json.loads(redisCache.get(userName))
        b1 = datetime.now()
        c1=b1-a1
        with open('d:/cacheTimeLaps1.txt','w') as myfile:
            myfile.write(str(c1.microseconds))
        if unpacked_check_result: # Checks the Cache
            return render_template('Check_History.html', check_results = unpacked_check_result)
    except TypeError:
        print('No cache was found')
    
    cursor = db.cursor()
    sql = 'SELECT * FROM accounts WHERE username = %s'
    cursor.execute(sql,userName )
    account = cursor.fetchone()    
    userID=account['id']
    cursor.execute(sql, str(session['username']))
    sql='select * from check_history where user_id=%s order by id desc;'
    a2 = datetime.now()
    cursor.execute(sql,(userID))
    s = cursor.fetchone()
    b2 = datetime.now()
    c2=b2-a2
    with open('d:/cacheTimeLaps2.txt','w') as myfile:
        myfile.write(str(c2.microseconds))
    if s:
        label=s['label']
        accuracy=s['accuracy']
        fileName=s['fName']
        return render_template('predict.html', image_file_name = fileName, label=label , accuracy = accuracy)
    else:
        return render_template('NoLastSearchFound.html', pageMessage='No Search Has Been Recorded For This User!')
    

@app.route('/check_history')
def checkHistory():
    cursor = db.cursor()
    sql = 'SELECT * FROM accounts WHERE username = %s order by id;'
    cursor.execute(sql, str(session['username']))
    account = cursor.fetchone()
    userID=account['id']
    cursor.execute(sql, str(session['username']))
    sql='select * from check_history where user_id=%s order by ID desc;'
    cursor.execute(sql,(userID))
    checkResults = cursor.fetchall()
		# the connection is not autocommited by default. So we must commit to save our changes.
    if checkResults:
        return render_template('Check_History.html', check_results = checkResults)
    else:
        return render_template('NoLastSearchFound.html', pageMessage='No Search Has Been Recorded For This User!')


@app.route('/check', methods=['POST','GET'])
def check():
	
	if request.method == 'GET':
		return render_template('check.html', staticURL= staticURL)

	else:
		cursor = db.cursor()
		file = request.files['image']
		t=datetime.now().microsecond
		checked_at=str(datetime.now())
		fileName=session['username']+'_'+str(t)+'_'+file.filename
		full_name = os.path.join(UPLOAD_FOLDER, fileName)
		file.save(full_name)
		result = predictML(full_name)
		accuracy= result[1]*100.0
		label = result[0]
		sql = 'SELECT * FROM accounts WHERE username = %s'
		userName=str(session['username'])
		cursor.execute(sql, userName )
		account = cursor.fetchone()
		userID=account['id']
		check=[{"userID":userID , "label":label, "accuracy": accuracy, "fName":fileName, "fAdrress":full_name, "checked_at":checked_at }]
		sql="""INSERT INTO check_history VALUES (NULL, %s , %s , %s , %s, %s, %s)"""
		cursor.execute(sql,(userID, label, accuracy, fileName, full_name, checked_at))
		# the connection is not autocommited by default. So we must commit to save our changes.
		db.commit()
		json_check = json.dumps(check)
		redisCache.set(userName, json_check)
		return render_template('predict.html', image_file_name = fileName, label=label , accuracy = accuracy)
 
 
@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename) 

 

if __name__ == '__main__':
    app.debug = True
    app.run(debug=True)
    app.debug = True
	