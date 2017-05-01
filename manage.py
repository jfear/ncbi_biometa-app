#!/usr/bin/env python
from flask_script import Manager
from biometa_app import create_app
from biometa_app.models import db

app = create_app('biometa_app.config.DevConfig')
manager = Manager(app)


@manager.shell
def make_shell_context():
    """ Creates a python REPL with several default imports
    in the context of the app.
    """
    return dict(app=app, db=db)


if __name__ == "__main__":
    manager.run()
