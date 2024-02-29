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

#default route can change later
@app.route('/')
def index():
    return redirect('login')

#not implemented yet
@app.route('/<user>/calendar')
def calendar():
    return render_template('calendar.html')

#returns a personalized home screen
@app.route('/home/<string:username>', methods=['GET', 'POST'])
#@login_required
def home(username):
    form = TaskAddForm(request.form)
    cnx = mysql.connector.connect(user='root', password='123', database='calendardb')
    cur = cnx.cursor()
    cur.execute(f"SELECT * FROM user WHERE username = '{username}'")
    user = cur.fetchone()
    userid = user[0]
    #gets all tasks that the user created
    cur.execute(f"SELECT * FROM tasks WHERE user_id = '{userid}'")
    tasks = cur.fetchall()
    cur.close()

    #for the weather
    CITY = user[6]
    print("base: " + BASE_URL)
    print("base212: " + API_KEY)
    print("city: " + CITY)
    url = BASE_URL + "appid=" + API_KEY + "&q=" + CITY
    response = requests.get(url).json()
    #number list
    weather = [round(keltoC(response['main']['temp']), 1), round(keltoC(response['main']['feels_like']), 1)]
    #string list
    weatherS = [response['weather'][0]['description'], response['sys']['country'], response['name']]
    
    
    if request.method == "POST":
        task = Tasks(user_id = userid, task = form.task.data)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('home', username=username))
    return render_template('home.html', user = user, tasks = tasks, form=form, weather=weather, weatherS=weatherS)

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
        print(pwd)
        print(user[1])
        if user:
            if pwd == user[1]: #hash password later on
                print()
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
        user = User(username = form.username.data, password = form.password.data, email = form.email.data,
                    fname = form.fname.data, lname = form.lname.data, city = form.city.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html", form=form)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(80))
    email = db.Column(db.String(64))
    fname = db.Column(db.String(64))
    lname = db.Column(db.String(64))
    city = db.Column(db.String(64))

    tasks = db.relationship("Tasks", backref='user')
    
class Tasks(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    task = db.Column(db.String(64))
    date_completed = db.Column(db.DateTime())


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
