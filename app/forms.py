from wtforms import StringField, SubmitField, validators, Form, PasswordField, SelectField, ValidationError
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo, DataRequired
from wtforms.fields.datetime import DateField
from .city import city

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

class Reset(Form):
     password= PasswordField('Password:', validators=[validators.InputRequired()])