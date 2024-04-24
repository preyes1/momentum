from .forms import UserAddForm, UserLogin
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
from .models import User
from app import db


auth = Blueprint('auth', __name__)

@auth.route("/login", methods=['GET', 'POST'])
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
                return redirect(url_for('views.home', username = user.username))
    return render_template("login.html", form=form)

#register page
@auth.route('/register', methods=['GET', 'POST'])
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
                return redirect(url_for('views.home', username = form.username.data))
        
    return render_template("register.html", form=form)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/login')