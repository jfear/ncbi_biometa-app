from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import current_user
from flask_principal import identity_loaded, UserNeed, RoleNeed

from app.models import db
from app.extensions import login_manager, principal
from app.main import main_bp
from app.auth import auth_bp
from app.attribute import attribute_bp

bootstrap = Bootstrap()

def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    principal.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(attribute_bp)


    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        # Set the identity user object
        identity.user = current_user

        # Add the UserNeed to the identity
        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))

        # Add each role to the identity
        if hasattr(current_user, 'roles'):
            for role in current_user.roles:
                identity.provides.add(RoleNeed(role))

    return app

if __name__ == "__main__":
    app.run()
