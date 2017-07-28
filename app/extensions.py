from flask import session
from flask_login import LoginManager
from flask_principal import Principal, Permission, RoleNeed, Identity
from app.models import User, Anonymous
from bson import ObjectId

login_manager = LoginManager()
login_manager.anonymous_user = Anonymous
login_manager.login_view = "auth.login"

principal = Principal(use_sessions=False)
admin_permission = Permission(RoleNeed('admin'))
default_permission = Permission(RoleNeed('default'))


# From: https://github.com/mattupstate/flask-principal/issues/40
@principal.identity_loader
def my_session_identity_loader():
    if 'identity_id' in session and 'identity_auth_type' in session:
        return Identity(session['identity_id'], session['identity_auth_type'])


@principal.identity_saver
def my_session_identity_saver(identity):
    session['identity_id'] = identity.id
    session['identity_auth_type'] = identity.auth_type
    session.modified = True


@login_manager.user_loader
def load_user(userid):
    return User.objects(pk=userid).first()
