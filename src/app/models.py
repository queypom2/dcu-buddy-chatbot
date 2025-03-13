from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy import ForeignKey, DateTime
from flask_bootstrap import Bootstrap 
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.widgets import TextInput
from wtforms.validators import InputRequired, Email, Length, ValidationError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from resources import valid_courses
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.static_folder = 'static'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(50), unique=True)
    coursecode = db.Column(db.String(15))
    password = db.Column(db.String(80))

    @validates('coursecode')
    def convert_upper(self, key, value):
        return value.upper()

class AssignmentTray(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    time_created = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

class AssignmentTrayItems(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tray_id = db.Column(db.Integer, db.ForeignKey(AssignmentTray.id))
    assignment_name = db.Column(db.String(50))
    due_date = db.Column(db.String(50))

class LoginForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    coursecode = StringField('coursecode', validators=[InputRequired(), Length(min=3, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])

    def validate_coursecode(form, coursecode):
        if coursecode.data.upper() not in valid_courses.courses:
           raise ValidationError("not valid course")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose another.')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))