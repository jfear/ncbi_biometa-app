from flask_mongoengine import MongoEngine

db = MongoEngine()

class AttributeValue(db.EmbeddedDocument):
    name = db.StringField()
    synonyms = db.ListField(default=list)

class AttributeSelector(db.Document):
    user = db.StringField(primary_key=True)
    attributes = db.ListField(db.EmbeddedDocumentField(AttributeValue), default=list)
