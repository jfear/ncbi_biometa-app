from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, FloatField, BooleanField, StringField
from wtforms import validators
from flask_mongoengine.wtf import model_form

from biometalib.models import CLEANED_ATTRIBUTES
from collections import OrderedDict


class PerPageForm(FlaskForm):
    per_pages = SelectField(
        'Number Per Page',
        choices=[(20, '20'), (40, '40'), (60, '60'), (100, '100')],
    )
    submit = SubmitField('Submit')


class QuerySampleAttribute(FlaskForm):
    SRR = StringField()
    SRX = StringField()
    Attributes = StringField()
    search = SubmitField('Search')


def message(fields):
    attrs = OrderedDict()
    for k, v in fields.items():
        if v['type'] == 'string':
            attrs[k] = StringField(k, description=v['description'])
        elif v['type'] == 'int':
            attrs[k] = IntegerField(k, description=v['description'])
        elif v['type'] == 'float':
            attrs[k] = FloatField(k, description=v['description'])
        elif v['type'] == 'bool':
            attrs[k] = BooleanField(k, description=v['description'])

    attrs['submit'] = SubmitField()
    return attrs

AttributeForm = type('AttributeForm', (FlaskForm,), message(CLEANED_ATTRIBUTES))
