from flask_mongoengine import MongoEngine

db = MongoEngine()

class AttributeValue(db.EmbeddedDocument):
    name = db.StringField()
    synonym = db.StringField()

class AttributeSelector(db.Document):
    user = db.StringField(primary_key=True)
    attributes = db.ListField(db.EmbeddedDocumentField(AttributeValue), default=list)
    index = db.DictField()
