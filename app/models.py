from . import db
from flask_login import UserMixin

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