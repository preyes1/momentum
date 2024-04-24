import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, request, redirect, jsonify, Blueprint
from flask_login import UserMixin, login_user, login_required, LoginManager, logout_user, current_user
from wtforms import StringField, SubmitField, validators, Form, PasswordField, SelectField, ValidationError
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo, DataRequired
from wtforms.fields.datetime import DateField
import mysql.connector
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from datetime import datetime as dt
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from .methods import date_to_string, date_to_string_FULL, keltoC
from app import db
from .forms import TaskAddForm, FriendAddForm, Reset, UserAddForm
from .models import User, Tasks, Friends, Requests

views = Blueprint('views', __name__)

# weather api
BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
# so that the key doesn't get exposed to people on GitHub
# "open api_key in reading mode, then read() the content of the file"
# API_KEY = open('api_key', 'r').read()
API_KEY = "28f6a4de82e7310e8a53a422bee18322"

GLOBAL_DATE = ""

@views.route('/')
def index():
    return render_template('about.html')

#gets json from javascript 
@views.route('/process', methods=['GET', 'POST'])
def process():
    data = request.get_json()
    date = data['value']
    #date is in "YYYY MM DD" format
    global GLOBAL_DATE
    GLOBAL_DATE = date
    return redirect(url_for('views.home', username = current_user.username))
    
@views.route('/addseconds', methods=['GET', 'POST'])
def addSeconds():
    data = request.get_json()
    seconds = data['value']
    cnx = mysql.connector.connect(host="creativename-db.cr8eauc2qc9a.us-east-2.rds.amazonaws.com", user='preyes1', password='4BevQ1NL9fxQkDMwn2Rh', database='creativename-db')
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
    
    return redirect(url_for('views.home', username = current_user.username))
 

#returns a personalized home screen
@views.route('/home/<username>', methods=['GET', 'POST'])
@login_required
def home(username):
    form = TaskAddForm(request.form)
    cnx = mysql.connector.connect(host="creativename-db.cr8eauc2qc9a.us-east-2.rds.amazonaws.com", user='preyes1', password='4BevQ1NL9fxQkDMwn2Rh', database='creativename-db')
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
        return redirect(url_for('views.home', username = current_user.username))
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
@views.route("/deletetask/<int:task_id>")
def deleteTask(task_id):
    task = Tasks.query.get_or_404(task_id)
    user = User.query.get_or_404(task.user_id)
    try:
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('views.home', username = user.username))
    except:
        return "error"

#changes task completed to True
@views.route("/checkbox/<int:task_id>")
def checkTask(task_id):
    task = Tasks.query.get_or_404(task_id)
    if task.completed:
        task.completed = False
    else:
        task.completed = True
    try:
        db.session.commit()
        return redirect(url_for('views.home', username = current_user.username))
    except:
        return "error"

@views.route("/lock/<task>")
@login_required
def lockin(task):
    return render_template("lockin.html", task=task, username=current_user.username)

#View Users (admin page)
@views.route("/adminView")
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
        return redirect(url_for('views.home', username = current_user.username))

@views.route("/deleteUser/<int:id>")
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
        return redirect(url_for('views.home', username = current_user.username))


@views.route("/userRole/<int:id>")
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
        return redirect(url_for('views.home', username = current_user.username))
    
@views.route("/friends", methods=['GET', 'POST'])
@login_required
def friends():
    form = FriendAddForm(request.form)
    cnx = mysql.connector.connect()
    cnx = mysql.connector.connect(host="creativename-db.cr8eauc2qc9a.us-east-2.rds.amazonaws.com", user='preyes1', password='4BevQ1NL9fxQkDMwn2Rh', database='creativename-db')
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
        cnx = mysql.connector.connect(host="creativename-db.cr8eauc2qc9a.us-east-2.rds.amazonaws.com", user='preyes1', password='4BevQ1NL9fxQkDMwn2Rh', database='creativename-db')

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

@views.route("/acceptfriend/<int:id>")
@login_required
def acceptFriend(id):
    user = User.query.get_or_404(id)
    # request_ = Requests.query.get_or_404(user.id) <-- this shouldnt work
    cnx = mysql.connector.connect()
    cnx = mysql.connector.connect(host="creativename-db.cr8eauc2qc9a.us-east-2.rds.amazonaws.com", user='preyes1', password='4BevQ1NL9fxQkDMwn2Rh', database='creativename-db')
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
    return redirect(url_for('views.friends'))

@views.route("/rejectfriend/<int:id>")
@login_required
def rejectFriend(id):
    user = User.query.get_or_404(id)
    # request_ = Requests.query.get_or_404(user.id) <-- this shouldnt work
    cnx = mysql.connector.connect()
    cnx = mysql.connector.connect(host="creativename-db.cr8eauc2qc9a.us-east-2.rds.amazonaws.com", user='preyes1', password='4BevQ1NL9fxQkDMwn2Rh', database='creativename-db')
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
    return redirect(url_for('views.friends'))

@views.route("/unfriend/<int:id>")
@login_required
def unFriend(id):
    user = User.query.get_or_404(id)
    # request_ = Requests.query.get_or_404(user.id) <-- this shouldnt work
    cnx = mysql.connector.connect()
    cnx = mysql.connector.connect(host="creativename-db.cr8eauc2qc9a.us-east-2.rds.amazonaws.com", user='preyes1', password='4BevQ1NL9fxQkDMwn2Rh', database='creativename-db')
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
    return redirect(url_for('views.friends'))

@views.route("/account", methods=['GET','POST'])
@login_required
def viewaccount():
    form = UserAddForm(request.form)
    user_to_update = User.query.get_or_404(current_user.id)
    form.username.data = user_to_update.username
    form.email.data = user_to_update.email
    form.fname.data = user_to_update.fname
    form.lname.data = user_to_update.lname
    form.city.data = user_to_update.city

    if request.method == 'POST':
        user_to_update.username = request.form['username']
        user_to_update.email = request.form['email']
        user_to_update.fname = request.form['fname']
        user_to_update.lname = request.form['lname']
        user_to_update.city = request.form['city']

        try:
            db.session.commit()
            return redirect("/account")
        except:
            return redirect("/account")
    else:
        return render_template("account.html", form = form, id=current_user.id)

#Reset Password
@views.route("/reset", methods=['POST', 'GET'])
def reset():
    form = Reset(request.form)
    if request.method == 'POST':
        user_to_update = User.query.get_or_404(current_user.id)
        user_to_update.password = generate_password_hash(form.password.data, method="pbkdf2:sha256")
        try:
            db.session.commit()
            logout_user()
            return redirect(url_for('auth.login'))
        except:
            return redirect(url_for('views.reset'))
    return render_template("reset.html", form=form)