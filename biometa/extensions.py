from flask_login import LoginManager
from flask_principal import Principal, Permission, RoleNeed
from biometa.models import User
from bson import ObjectId

login_manager = LoginManager()
login_manager.login_view = "auth.login"

principal = Principal()
admin_permission = Permission(RoleNeed('admin'))
default_permission = Permission(RoleNeed('default'))

@login_manager.user_loader
def load_user(userid):
    return User.objects(pk=userid).first()
