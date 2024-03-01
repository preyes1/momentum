import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_login import UserMixin, login_user, login_required, LoginManager, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators, Form, PasswordField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError
from wtforms.fields.datetime import DateField
from wtforms.fields import TimeField
from datetime import datetime
import mysql.connector
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
import datetime as dt
import requests
from werkzeug.security import generate_password_hash, check_password_hash

#weather api
BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
API_KEY = "15df869839c74281f7b1914adbc67201"

def keltoC(degrees):
    return degrees - 273.15
#list of available cities
city = ['Toronto', 'New York City', 'Los Angeles', 'Chicago', 'Ottawa', "Vancouver", "Tokyo"]




app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'hard to guess string' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123@localhost/calendardb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app,db)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

#default route can change later
@app.route('/')
def index():
    return redirect('login')

#not implemented yet
@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

#returns a personalized home screen
@app.route('/home/<string:username>', methods=['GET', 'POST'])
@login_required
def home(username):
    form = TaskAddForm(request.form)
    cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
    cur = cnx.cursor()
    cur.execute(f"SELECT * FROM user WHERE username = '{username}'")
    user = cur.fetchone()
    userid = user[0]
    #gets all tasks that the user created
    cur.execute(f"SELECT * FROM tasks WHERE id = '{userid}'")
    tasks = cur.fetchall()
    cur.close()

    #for the weather
    CITY = user[6]
    url = BASE_URL + "appid=" + API_KEY + "&q=" + CITY
    response = requests.get(url).json()
    #number list
    weather = [round(keltoC(response['main']['temp']), 1), round(keltoC(response['main']['feels_like']), 1)]
    #string list
    weatherS = [response['weather'][0]['description'], response['sys']['country'], response['name']]
    
    
    if request.method == "POST":
        task = Tasks(id = userid, task = form.task.data)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('home', username=username))
    return render_template('home.html', user = user, tasks = tasks, form=form, weather=weather, weatherS=weatherS)

@app.route("/deletetask/<int:task_id>")
def deleteTask(task_id):
    task = Tasks.query.get_or_404(task_id)
    user = User.query.get_or_404(task.id)
    try:
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('home', username = user.username))
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
        print(user.username)
        if user:
            if check_password_hash(user.password, pwd):
                flash("Login Successful", category='success')
                login_user(user, remember=True)
                return redirect(url_for('home', username=username))
            else:
                flash("Wrong Password!")
        else:
            flash("Username is wrong!")
            
    return render_template("login.html", form=form)

#register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserAddForm(request.form)
    if request.method == "POST":
        email_exists = User.query.filter_by(email=form.email.data).first()
        username_exists = User.query.filter_by(username=form.username.data).first()

        if email_exists:
            flash("Email already exists", category="error")
        elif username_exists:
            flash("Username already exists", category="error")
        else:
            user = User(username = form.username.data, password = generate_password_hash(form.password.data, method='pbkdf2:sha256'), email = form.email.data,
                        fname = form.fname.data, lname = form.lname.data, city = form.city.data)
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash("User Created")
            return redirect(url_for('home', username = form.username.data))
        
    return render_template("register.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(150))
    email = db.Column(db.String(64), unique=True)
    fname = db.Column(db.String(64))
    lname = db.Column(db.String(64))
    city = db.Column(db.String(64))

    tasks = db.relationship("Tasks", backref='user')
    events = db.relationship("Events", backref='user')
    
class Tasks(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task = db.Column(db.String(64))
    date_completed = db.Column(db.DateTime())

class Events(db.Model):
    __tablename__ = 'events'
    event_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event = db.Column(db.String(64))
    start = db.Column(db.DateTime())
    end = db.Column(db.DateTime())

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
    start = DateField("Start", validators=[validators.InputRequired()])
    end = DateField("End", validators=[validators.InputRequired()])
