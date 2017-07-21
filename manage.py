#!/usr/bin/env python
import os
from flask_script import Manager, Server
from app import create_app
from app.models import db

app = create_app('app.config.DevConfig')
manager = Manager(app)
manager.add_command("runserver", Server(host="0.0.0.0", port=80))

@manager.shell
def make_shell_context():
    """ Creates a python REPL with several default imports
    in the context of the app.
    """
    return dict(app=app, db=db)


if __name__ == "__main__":
    manager.run()
