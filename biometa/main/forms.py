from flask_wtf import Form
from wtforms import SelectField, SubmitField, TextField
from wtforms import validators


class PerPageForm(Form):
    per_pages = SelectField(
        'Number Per Page',
        choices=[(20, '20'), (40, '40'), (60, '60'), (100, '100')],
    )
    submit = SubmitField('Submit')

class TestForm(Form):
    autocomp = TextField(
        'autocomp',
        id='autocomplete'
    )
    selection = SelectField(
        'selection',
        choices=[(20, '20'), (40, '40'), (60, '60'), (100, '100')],
    )
