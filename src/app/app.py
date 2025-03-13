from tkinter import Widget
from types import new_class
from chatterbot import ChatBot
from chatbot import chatbot
from flask import Flask, render_template, redirect, session, url_for, request
from flask_bootstrap import Bootstrap 
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.widgets import TextInput
from wtforms.validators import InputRequired, Email, Length, ValidationError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime
from models import *
from timetable import *
import time
from resources import valid_courses

timetable_prompts = {
    "Here is your timetable for today :)": datetime.datetime.now().isoweekday() % 6,
    "Here is your timetable for tomorrow :)": (datetime.datetime.now().isoweekday() % 6) + 1,
    "Here is your timetable for monday :)": 1,
    "Here is your timetable for tuesday :)": 2,
    "Here is your timetable for wednesday :)": 3,
    "Here is your timetable for thursday :)": 4,
    "Here is your timetable for friday :)": 5
}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dcubuddy'))

        return '<h1>Invalid email or password</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(coursecode=form.coursecode.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return dcubuddy()
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form)

@app.route('/dcubuddy')
@login_required
def dcubuddy():
    return render_template('dcubuddy.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/get")
def get_bot_response():
    time.sleep(2)
    userText = request.args.get('msg').strip()
    text_split = userText.split()
    command = text_split[0]
    if command in commands:
        if len(text_split) == 3:
            return commands[command](text_split[1], text_split[2])
        elif len(text_split) == 2:
            return commands[command](text_split[1])
        else:
            try:
                return commands[command]()
            except IndexError:
                return "Sorry, too many arguments given to command."


    bot_response = str(chatbot.get_response(userText))
    if bot_response in timetable_prompts:
        return fetch_timetable(bot_response, timetable_prompts[bot_response])
    return bot_response

def update_course(course):
    if course.upper() not in valid_courses.courses:
        return "Sorry that is not a valid course."

    user = User.query.filter_by(id=current_user.id).first()
    user.coursecode = course.upper()
    db.session.commit()
    return "I have updated your course"

def add_assignment(name, date):
    assign_name = name
    due_date = date
    user = current_user.id

    assignment_tray = db.session.query(AssignmentTray).filter(AssignmentTray.user_id == user).first()
    if not assignment_tray:
        new_tray = AssignmentTray(user_id=user)
        db.session.add(new_tray)
        db.session.commit()
        assignment_tray = db.session.query(AssignmentTray).filter(AssignmentTray.user_id == user).first()

    new_assignment = AssignmentTrayItems(tray_id=assignment_tray.id, assignment_name=assign_name, due_date=due_date)
    db.session.add(new_assignment)
    db.session.commit()

    response = "Assignment added :)"
    return response

def delete_assignment(name):
    user = current_user.id
    assignment_tray = db.session.query(AssignmentTray).filter(AssignmentTray.user_id == user).first()
    if not assignment_tray:
        return "You have no assignments with this name"
    to_delete = db.session.query(AssignmentTrayItems).filter(AssignmentTrayItems.tray_id == assignment_tray.id, AssignmentTrayItems.assignment_name == name).first()

    print(to_delete)
    if not to_delete:
        return "You have no assignments with this name"

    db.session.query(AssignmentTrayItems).filter(AssignmentTrayItems.tray_id == assignment_tray.id, AssignmentTrayItems.assignment_name == name).delete()
    db.session.commit()

    response = "Assignment deleted :)"
    return response

def view_assignment():
    user = current_user.id
    assignment_tray = db.session.query(AssignmentTray).filter(AssignmentTray.user_id == user).first()
    all_assignments = db.session.query(AssignmentTrayItems).filter(AssignmentTrayItems.tray_id == assignment_tray.id).all()
    new_string = ""
    for assignment in all_assignments:
        new_string += "<br><br>" + assignment.assignment_name + "<br>" + assignment.due_date

    return "Here are your current assignments:" + new_string.strip()

commands =  {"!addassignment": add_assignment,
    "!deleteassignment": delete_assignment,
    "!viewassignments": view_assignment,
    "!updatecourse": update_course
}

def fetch_timetable(response, weekday):
    course = current_user.coursecode.upper()
    week = 1

    # if user ask for a day that has passed give them next week's timetable
    if weekday < datetime.datetime.now().isoweekday() % 6:
        week = 2
    # If user is asking for tomorrows timetable on a sunday
    if weekday == 8:
        weekday = 1
    reply = response + "<br><br>"
    timetable = get_timetable(course, weekday, week)
    if timetable == "":
        return "There are no classes on this day"
    reply += timetable

    return reply

if __name__ == '__main__':
    app.run(debug=True)