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


#not implemented anymore
#can use current_user.id to get the current user
@app.route('/calendar')
@login_required
def calendar():
    cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
    cur = cnx.cursor()
    cur.execute(f"SELECT * FROM events WHERE user_id = '{current_user.id}'")
    events = cur.fetchall()
    return render_template('calendar.html', events= events)

#not implemented anymore
@app.route("/calendar/add/<string:start>", methods=['GET', 'POST'])
@login_required
def add(start):
    form = EventAddForm(request.form)
    nstart = start[4:15] #15 for just time
    form.start1.data = dt.strptime(nstart, '%b %d %Y') #'%b %d %Y' for just date, '%b %d %Y %H:%M:%S'
    date1 = dt.strptime(nstart, '%b %d %Y') #'%b %d %Y' for just date, '%b %d %Y %H:%M:%S'
    form.start1.data = date1.strftime('%Y-%b-%d')
    form.start1.data = dt.strptime(form.start1.data, '%Y-%b-%d')
    if request.method == "POST":
        event = Events(user_id = current_user.id, event = form.event.data, start1 = form.start1.data, end = form.end.data)
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('calendar'))
    return render_template('eventAdd.html', form=form)
    
#gets json from javascript 
@app.route('/process', methods=['GET', 'POST'])
def process():
    data = request.get_json()
    date = data['value']
    #date is in "YYYY MM DD" format
    global GLOBAL_DATE
    GLOBAL_DATE = date
    return redirect(url_for('home', username = current_user.username))
    
 

#returns a personalized home screen
@app.route('/<username>', methods=['GET', 'POST'])
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
    print(GLOBAL_DATE)
    if GLOBAL_DATE != '':
        cur.execute(f"SELECT * FROM tasks WHERE user_id = '{userid}' AND date = '{GLOBAL_DATE}'")
        print("tried")
    else:
        cur.execute(f"SELECT * FROM tasks WHERE user_id = '{userid}' AND date = '{current_date_raw}'")
        print("did this instead")
    tasks = cur.fetchall()
    print(tasks)
    #sorts list, tasks that are completed are at the end (so that they appear first)
    tasks = sorted(tasks, key=lambda x: x[3], reverse=True)
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

    print(form.task.data)
    print(f'{GLOBAL_DATE} hello is the most')
    if request.method == "POST" and form.task.data is not None:
        print("did you reall post?")
        if GLOBAL_DATE != "":
            task = Tasks(user_id = userid, task = form.task.data, date=GLOBAL_DATE)
            db.session.add(task)
            db.session.commit()
            print("posted global")
        else:
            task = Tasks(user_id = userid, task = form.task.data, date=current_date_raw)
            db.session.add(task)
            db.session.commit()
            print("posted current_date_raw")
        return redirect(url_for('home', username = current_user.username))
    #reverses tasks so the newest task will be at the top
    tasks.reverse()
    print("got here")
    return render_template('home.html', user = user, tasks = tasks, form=form, 
                           weather=weather, weatherS=weatherS, current_date = current_date,
                           current_date_full = current_date_full, global_date = GLOBAL_DATE)

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

