from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField, BooleanField, StringField
from wtforms import validators

class AttributeSelector(FlaskForm):
    KeepButton = SubmitField('Keep', description="Click to keep current attribute type.")
    IgnoreButton = SubmitField('Ignore', description="Click to ignore current attribute type.")
    RenameButton = SubmitField('Rename', description="Click to Rename current attribute type.")
    Rename= StringField('Rename To', descritpion="Rename the current attribute to this value.")
