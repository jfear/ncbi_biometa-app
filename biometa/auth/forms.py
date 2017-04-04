from flask_mongoengine.wtf import model_form
from flask_wtf import Form
from wtforms import TextAreaField, TextField, PasswordField, StringField, SubmitField
from wtforms import validators, ValidationError
from ..models import User


class RegisterForm(Form):
    username = StringField(
        'Username',
        validators=[validators.DataRequired()]
    )

    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.objects(username=field.data).first():
           raise ValidationError('Username already exists.')

        return True


class LoginForm(Form):
    username = StringField(
        'Username',
        validators=[validators.DataRequired()]
    )

    submit = SubmitField('Log In')
