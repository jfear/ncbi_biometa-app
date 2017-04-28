from flask_mongoengine import MongoEngine
from flask_mongoengine.wtf import model_form
from flask_login import UserMixin

from sramongo.mongo_schema import Pubmed

db = MongoEngine()


class User(db.Document, UserMixin):
    username = db.StringField(unique=True, required=True)
    roles = db.ListField(db.StringField(), default=list)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Contacts(db.EmbeddedDocument):
    first_name = db.StringField()
    last_name = db.StringField()
    email = db.StringField()


class Experiment(db.EmbeddedDocument):
    srx = db.StringField()
    runs = db.ListField(db.StringField(), default=list)


class Annotation(db.EmbeddedDocument):
    name = db.StringField()
    value = db.StringField()


class Biometa(db.Document):
    biosample = db.StringField(primary_key=True, required=True)
    srs = db.StringField()
    gsm = db.StringField()
    srp = db.StringField()
    bioproject = db.StringField()
    study_title = db.StringField()
    study_abstract = db.StringField()
    description = db.StringField()

    contacts = db.ListField(db.EmbeddedDocumentField(Contacts), default=list)
    papers = db.ListField(db.EmbeddedDocumentField(Pubmed), default=list)
    experiments = db.ListField(db.EmbeddedDocumentField(Experiment), default=list)

    taxon_id = db.StringField()
    sample_title = db.StringField()
    sample_attributes = db.ListField(db.EmbeddedDocumentField(Annotation), default=list)

    magic = db.ListField(db.EmbeddedDocumentField(Annotation))
    mieg = db.ListField(db.EmbeddedDocumentField(Annotation))
    chen = db.ListField(db.EmbeddedDocumentField(Annotation))
    oliver = db.ListField(db.EmbeddedDocumentField(Annotation))
    nlm = db.ListField(db.EmbeddedDocumentField(Annotation))
    fear = db.ListField(db.EmbeddedDocumentField(Annotation))
