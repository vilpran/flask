from flask import Blueprint, render_template

views = Blueprint('views',__name__)

@views.route('/login/')
def login():
    render_template("login.html")