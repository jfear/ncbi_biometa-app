from flask_wtf import Form
from wtforms import SelectField, SubmitField, TextField, FieldList, StringField
from wtforms import validators


class TestForm(Form):
    autocomp = TextField(
        'autocomp',
        id='autocomplete'
    )
    selection = SelectField(
        'selection',
        choices=[(20, '20'), (40, '40'), (60, '60'), (100, '100')],
    )


class TestFormTwo(Form):
    testList = FieldList(TextField('Name'), min_entries=2)


class PerPageForm(Form):
    per_pages = SelectField(
        'Number Per Page',
        choices=[(20, '20'), (40, '40'), (60, '60'), (100, '100')],
    )
    submit = SubmitField('Submit')
