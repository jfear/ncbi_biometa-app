from flask import render_template, redirect, request, flash, url_for, current_app
from flask_login import login_user, logout_user, login_required
from . import auth_bp
from ..models import db, User
from .forms import RegisterForm, LoginForm
from ..extensions import admin_permission
from flask_principal import Identity, AnonymousIdentity, identity_changed

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.objects(username=form.username.data).first()

        login_user(user)
        identity_changed.send(
            current_app._get_current_object(),
            identity=Identity(str(user.pk))
        )

        flash("Logged in successfully.", "success")
        return redirect(request.args.get("next") or url_for("main.home"))

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    identity_changed.send(
        current_app._get_current_object(),
        identity=AnonymousIdentity()
    )

    return redirect(url_for('main.home'))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == 'POST' and form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.save()
#         default_role = Role.query.filter_by(name="default").first()
#         user.roles.append(default_role)

        flash("Your user has been created, please login.", category="success")
        return redirect(url_for(".register"))

    return render_template("register.html", form=form)
