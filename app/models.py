from flask_mongoengine import MongoEngine, BaseQuerySet
from flask_mongoengine.pagination import ListFieldPagination
from flask_mongoengine.wtf import model_form
from flask_login import UserMixin
import types

from biometalib.models import BiometaFields

db = MongoEngine()


class User(db.Document, UserMixin):
    username = db.StringField(unique=True, required=True)
    roles = db.ListField(db.StringField(), default=list)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Biometa(db.Document, BiometaFields):
    pass

