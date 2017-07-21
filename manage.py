#!/usr/bin/env python
import os
from flask_script import Manager
from app import create_app
from app.models import db

# set up environmental variables
with open(".env", 'r') as fh:
    for pair in fh:
        key, value = pair.strip().split('=')
        os.environ[key] = value

app = create_app('app.config.DevConfig')
manager = Manager(app)


@manager.shell
def make_shell_context():
    """ Creates a python REPL with several default imports
    in the context of the app.
    """
    return dict(app=app, db=db)


if __name__ == "__main__":
    manager.run()
