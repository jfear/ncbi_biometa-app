from flask import render_template, redirect, request, flash, url_for, current_app
from . import main_bp
from ..models import db, User, Biometa
from ..extensions import admin_permission

@main_bp.route("/")
def home():
    return render_template('index.html', )
