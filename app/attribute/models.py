from flask_mongoengine import MongoEngine

db = MongoEngine()

class AttributeSelector(db.Document):
    data = db.DictField()
