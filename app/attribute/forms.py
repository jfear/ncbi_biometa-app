from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField, BooleanField, StringField
from wtforms import validators

class AttributeSelectorForm(FlaskForm):
    KeepButton = SubmitField('Keep')
    IgnoreButton = SubmitField('Ignore')
    Rename= StringField('Rename To', description="Rename the current attribute to this value.")
    RenameButton = SubmitField('Rename')

class AttributePager(FlaskForm):
    Previous = SubmitField('Previous')
    Next = SubmitField('Next')
