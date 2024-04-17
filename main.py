import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, request, redirect, jsonify
from flask_login import UserMixin, login_user, login_required, LoginManager, logout_user, current_user
from wtforms import StringField, SubmitField, validators, Form, PasswordField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError
from wtforms.fields.datetime import DateField
import mysql.connector
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from datetime import datetime as dt
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from methods import date_to_string, date_to_string_FULL, keltoC
from city import city

#weather api
BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
#so that the key doesn't get exposed to people on GitHub
#"open api_key in reading mode, then read() the content of the file"
API_KEY = open('api_key', 'r').read()

GLOBAL_DATE = ""

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'hard to guess string' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123@localhost/calendardb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True
db = SQLAlchemy(app)
migrate = Migrate(app,db)

#user authentication stuff
login_manager = LoginManager()
login_manager.login_view = "index"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

#default route redirects user to login page
@app.route('/')
def index():
    return render_template('about.html')

#gets json from javascript 
@app.route('/process', methods=['GET', 'POST'])
def process():
    data = request.get_json()
    date = data['value']
    #date is in "YYYY MM DD" format
    global GLOBAL_DATE
    GLOBAL_DATE = date
    return redirect(url_for('home', username = current_user.username))
    
@app.route('/addseconds', methods=['GET', 'POST'])
def addSeconds():
    data = request.get_json()
    seconds = data['value']
    cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
    cur = cnx.cursor()
    cur.execute(f"SELECT * FROM user WHERE username = '{current_user.username}'")
    user = cur.fetchone()
    if user[8]:
        user_seconds = user[8] + seconds
    else:
        user_seconds = seconds
    current_user.seconds = user_seconds
    try:
        db.session.commit()
        
    except:
        return "error"
    
    return redirect(url_for('home', username = current_user.username))
 

#returns a personalized home screen
@app.route('/home/<username>', methods=['GET', 'POST'])
@login_required
def home(username):
    form = TaskAddForm(request.form)
    cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
    cur = cnx.cursor()
    cur.execute(f"SELECT * FROM user WHERE username = '{current_user.username}'")
    user = cur.fetchone()
    userid = user[0]
    #gets all tasks that the user created
    current_date_raw = dt.now().strftime('%Y-%m-%d')
    if GLOBAL_DATE != '':
        cur.execute(f"SELECT * FROM tasks WHERE user_id = '{userid}' AND date = '{GLOBAL_DATE}'")
    else:
        cur.execute(f"SELECT * FROM tasks WHERE user_id = '{userid}' AND date = '{current_date_raw}'")
    tasks = cur.fetchall()
    #sorts list, tasks that are completed are at the end (so that they appear first)
    tasks = sorted(tasks, key=lambda x: x[3], reverse=True)
    seconds = user[8]
    cur.close()

   

    #for the weather
    CITY = user[6]
    url = BASE_URL + "appid=" + API_KEY + "&q=" + CITY
    response = requests.get(url).json()
   
    #number list
    weather = [round(keltoC(response['main']['temp']), 1), round(keltoC(response['main']['feels_like']), 1)]
    #string list
    weatherS = [response['weather'][0]['description'], response['sys']['country'], response['name']]
    
    current_date = date_to_string(current_date_raw)
    current_date_full = date_to_string_FULL(current_date_raw)

    if request.method == "POST" and form.task.data is not None:
        if GLOBAL_DATE != "":
            task = Tasks(user_id = userid, task = form.task.data, date=GLOBAL_DATE)
            db.session.add(task)
            db.session.commit()
        else:
            task = Tasks(user_id = userid, task = form.task.data, date=current_date_raw)
            db.session.add(task)
            db.session.commit()
        return redirect(url_for('home', username = current_user.username))
    #reverses tasks so the newest task will be at the top
    tasks.reverse()
    # Gets number of friends user has
    cur = cnx.cursor()
    cur.execute(f"SELECT * FROM friends WHERE user_id_1 = '{current_user.id}' OR user_id_2 = '{current_user.id}'")
    friends = cur.fetchall()
    cur.close()

    return render_template('home.html', user = user, tasks = tasks, form=form, 
                           weather=weather, weatherS=weatherS, current_date = current_date,
                           current_date_full = current_date_full, global_date = GLOBAL_DATE,
                            seconds = seconds, friends_count = len(friends))

#delete tasks
@app.route("/deletetask/<int:task_id>")
def deleteTask(task_id):
    task = Tasks.query.get_or_404(task_id)
    user = User.query.get_or_404(task.user_id)
    try:
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('home', username = user.username))
    except:
        return "error"

#changes task completed to True
@app.route("/checkbox/<int:task_id>")
def checkTask(task_id):
    task = Tasks.query.get_or_404(task_id)
    if task.completed:
        task.completed = False
    else:
        task.completed = True
    try:
        db.session.commit()
        return redirect(url_for('home', username = current_user.username))
    except:
        return "error"

#login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLogin(request.form)
    if request.method == "POST":
        username = form.username.data
        pwd = form.password.data
        cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
        cur = cnx.cursor()
        cur.execute(f"SELECT username, password FROM user WHERE username = '{username}'")
        user = cur.fetchone() #create something that happens if user inputs invalid details
        #user[0] is username, user[1] is password 
        cur.close()
        user = User.query.filter_by(username=username).first()
        if user:
            #could turn this into a verify_password() function
            if check_password_hash(user.password, pwd): 
                #logs in the user so they can access @login_required pages
                login_user(user, remember=True)
                return redirect(url_for('home', username = user.username))
    return render_template("login.html", form=form)

#register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserAddForm(request.form)
    if request.method == "POST":
        email_exists = User.query.filter_by(email=form.email.data).first()
        username_exists = User.query.filter_by(username=form.username.data).first()
        admin_exists = User.query.filter_by(id = 1).first()

        #if the email and username are unique
        if not email_exists:
            if not username_exists:
                user = User(username = form.username.data, password = generate_password_hash(form.password.data, method='pbkdf2:sha256'), email = form.email.data,
                            fname = form.fname.data, lname = form.lname.data, city = form.city.data)
                if not admin_exists:
                    user.role = 'ADMIN'
                else:
                    user.role = 'STANDARD'
                db.session.add(user)
                db.session.commit()
                #logs in the user so they don't have to input their info again to log in
                login_user(user, remember=True)
                return redirect(url_for('home', username = form.username.data))
        
    return render_template("register.html", form=form)

@app.route("/lock/<task>")
@login_required
def lockin(task):
    return render_template("lockin.html", task=task, username=current_user.username)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/login')

#View Users (admin page)
@app.route("/adminView")
@login_required
def adminView():
    if current_user.role == 'ADMIN':
        cnx = mysql.connector.connect(user = 'root', password='123', database='calendardb')
        cur = cnx.cursor()
        cur.execute("SELECT * FROM user")
        users = cur.fetchall()
        cur.close()
        return render_template("adminView.html", users = users)
    else:
        return redirect(url_for('home', username = current_user.username))

@app.route("/deleteUser/<int:id>")
@login_required
def deleteUser(id):
    if current_user.role == 'ADMIN':
        user_to_delete = User.query.get_or_404(id)
        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            return redirect("/adminView")
        except:
            return redirect("/adminView")
    else:
        return redirect(url_for('home', username = current_user.username))


@app.route("/userRole/<int:id>")
@login_required
def userRole(id):
    if current_user.role == 'ADMIN':
        user_to_update= User.query.get_or_404(id)
        if user_to_update.role == 'ADMIN':
            user_to_update.role = 'STANDARD'
        else:
            user_to_update.role = 'ADMIN'
        try:
            db.session.commit()
            return redirect("/adminView")
        except:
            return redirect("/adminView")
    else:
        return redirect(url_for('home', username = current_user.username))
    
@app.route("/friends", methods=['GET', 'POST'])
@login_required
def friends():
    form = FriendAddForm(request.form)
    cnx = mysql.connector.connect()
    cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
    cur = cnx.cursor()
    cur.execute(f"SELECT * FROM requests WHERE user_id_to = '{current_user.id}'")
    requests = cur.fetchall()
    i =0
    
    user_requests = []
    # cant use the variable name request because it is already set
    for request_ in requests:
        # for each friend request, get the user who sent them and
        # set it to the current request value (this is to get the 
        # sender's username)
        user_sent = User.query.get_or_404(request_[1])
        user_requests.append(user_sent)
        i += 1
    # get all friends
    cur.close()
    cur = cnx.cursor()
    cur.execute(f"SELECT * FROM friends WHERE user_id_1 = '{current_user.id}' OR user_id_2 = '{current_user.id}'")
    friends = cur.fetchall()
    i=0
    user_friends = []
    for friend in friends:
        # for each friend, check which column does not contain the 
        # current user's id then get the username of the user in 
        # the other column
        if friend[1] == current_user.id:
            cur_friend = User.query.get_or_404(friend[2])
            user_friends.append(cur_friend) 
        else:
            cur_friend = User.query.get_or_404(friend[1])
            user_friends.append(cur_friend) 
        i+=1

    cur.close()
    #sending friend request
    if request.method == "POST":
        username = form.request.data
        cnx = mysql.connector.connect()
        cnx = mysql.connector.connect(user='root', password='123', database='calendardb')

        # Checks if the username exists
        cur = cnx.cursor()
        cur.execute(f"SELECT username FROM user")
        usernames = cur.fetchall()
        cur.close()
        exists = False
        for username_for in usernames:
            if username_for[0] == username:
                exists = True
                break
        if exists:
            try:
                #3 validators with default values of True
                valid = True
                valid2 = True
                valid3 = True
                # checks if requested username is the user's username
                if username == current_user.username:
                    valid3 = False

                # Gets the user's id
                cur = cnx.cursor()
                cur.execute(f"SELECT id FROM user WHERE username = '{username}'")
                user = cur.fetchone()
                cur.close()
                # Gets list of all requests made from current user and user sending request to
                # this is to check if one of them have already sent a friend request to each other
                cur = cnx.cursor()
                cur.execute(f"SELECT * FROM requests WHERE user_id_from = '{current_user.id}' OR user_id_from = '{user}'")
                prev_requests = cur.fetchall()
                cur.close()
                # Gets list of all friends of the current user and the user sending the request to
                # this is to check if they are already friends
                cur = cnx.cursor()
                cur.execute(f"SELECT * FROM friends WHERE user_id_1 = '{current_user.id}' OR user_id_1 = '{user}'")
                prev_friends = cur.fetchall()
                cur.close()

                # for loop that checks if request has already been made
                for req in prev_requests:
                    
                    if req[1] == current_user.id and req[2] == user[0]:
                        valid = False
                        break
                    elif req[1] == user[0] and req[2] == current_user.id:
                        valid = False
                        break
                    else:
                        valid = True
                # for loop that checks if users are already friends
                for fri in prev_friends:
                    if fri[1] == current_user.id and fri[2] == user[0]:
                        valid2 = False
                        break
                    elif fri[1] == user[0] and fri[2] == current_user.id:
                        valid2 = False
                        break
                    else:
                        valid2 = True
                # If all 3 vaildators are true then the request can be sent
                if valid and valid2 and valid3:
                    request_to_add = Requests(user_id_from = current_user.id, user_id_to = user[0])
                    db.session.add(request_to_add)
                    db.session.commit()
                    form.request.data = ""
                else:
                    form.request.data = ""
                    return render_template("friends.html", form=form, requests=user_requests, friends=user_friends, friend_count=len(user_friends))
                    
                
            except:
                return "error"
        else:
            return render_template("friends.html", form=form, requests=user_requests, friends=user_friends, friend_count=len(user_friends))
        
    return render_template("friends.html", form=form, requests=user_requests, friends=user_friends, friend_count=len(user_friends))

@app.route("/acceptfriend/<int:id>")
@login_required
def acceptFriend(id):
    user = User.query.get_or_404(id)
    # request_ = Requests.query.get_or_404(user.id) <-- this shouldnt work
    cnx = mysql.connector.connect()
    cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
    cur = cnx.cursor(buffered=True)
    cur.execute(f"SELECT request_id FROM requests WHERE user_id_from = '{id}' AND user_id_to = '{current_user.id}'")
    request_from = cur.fetchone()
    request_from = Requests.query.get_or_404(request_from)
    cur.close()
    try:
        new_friend = Friends(user_id_1 = current_user.id, user_id_2 = user.id)
        db.session.add(new_friend)
        db.session.delete(request_from)
        db.session.commit()
        
    except:
        return "error"
    return redirect(url_for('friends'))

@app.route("/rejectfriend/<int:id>")
@login_required
def rejectFriend(id):
    user = User.query.get_or_404(id)
    # request_ = Requests.query.get_or_404(user.id) <-- this shouldnt work
    cnx = mysql.connector.connect()
    cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
    cur = cnx.cursor(buffered=True)
    cur.execute(f"SELECT request_id FROM requests WHERE user_id_from = '{id}' AND user_id_to = '{current_user.id}'")
    request_from = cur.fetchone()
    request_ = Requests.query.get_or_404(request_from)
    cur.close()
    try:
        db.session.delete(request_)
        db.session.commit()
        
    except:
        return "error"
    return redirect(url_for('friends'))

@app.route("/unfriend/<int:id>")
@login_required
def unFriend(id):
    user = User.query.get_or_404(id)
    # request_ = Requests.query.get_or_404(user.id) <-- this shouldnt work
    cnx = mysql.connector.connect()
    cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
    cur = cnx.cursor(buffered=True)
    cur.execute(f"SELECT friend_id FROM friends WHERE (user_id_1 = '{id}' AND user_id_2 = '{current_user.id}') OR (user_id_1 = '{current_user.id}' AND user_id_2 = '{id}')")
    friend_to_delete = cur.fetchone()
    friend_to_delete = Friends.query.get_or_404(friend_to_delete)
    cur.close()
    try:
        db.session.delete(friend_to_delete)
        db.session.commit()
        
    except:
        return "error"
    return redirect(url_for('friends'))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(150))
    email = db.Column(db.String(64), unique=True)
    fname = db.Column(db.String(64))
    lname = db.Column(db.String(64))
    city = db.Column(db.String(64))
    role = db.Column(db.String(64))
    seconds = db.Column(db.Integer, default=0)

    tasks = db.relationship("Tasks", backref='user')
    events = db.relationship("Events", backref='user')

class Tasks(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task = db.Column(db.String(64))
    completed = db.Column(db.Boolean, default = False)
    date = db.Column(db.String(64))

class Events(db.Model):
    __tablename__ = 'events'
    event_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event = db.Column(db.String(64))
    #cant name it start or else it will cause problems
    start1 = db.Column(db.Date())
    end = db.Column(db.Date())

class Friends(db.Model):
    __tablename__ = 'friends'
    friend_id = db.Column(db.Integer, primary_key=True)
    user_id_1 = db.Column(db.Integer)
    user_id_2 = db.Column(db.Integer)

class Requests(db.Model):
    __tablename__ = 'requests'
    request_id = db.Column(db.Integer, primary_key=True)
    user_id_from = db.Column(db.Integer)
    user_id_to = db.Column(db.Integer)

class UserAddForm(Form):
    username = StringField("Username", validators=[validators.InputRequired()])
    password = PasswordField("Password", validators=[validators.InputRequired()])
    email = StringField("Email", validators=[validators.InputRequired()])
    fname = StringField("First Name", validators=[validators.InputRequired()])
    lname = StringField("Last Name", validators=[validators.InputRequired()])
    city = SelectField("City", choices=city)
    

class UserLogin(Form):
    username = StringField("Username", validators=[validators.InputRequired()])
    password = PasswordField("Password", validators=[validators.InputRequired()])

class TaskAddForm(Form):
    task = StringField("Task", validators=[validators.InputRequired()])

class EventAddForm(Form):
    event = StringField("Event", validators=[validators.InputRequired()])
    start1 = DateField("Start", validators=[validators.InputRequired()])
    end = DateField("End", validators=[validators.InputRequired()])

class FriendAddForm(Form):
    request = StringField("Request", validators=[validators.InputRequired()])

