from flask_mongoengine.wtf import model_form
from flask_wtf import Form
from wtforms import TextAreaField, TextField, PasswordField, StringField
from wtforms import validators
from ..models import User


class RegisterForm(Form):
    username = TextField(
        'Username',
        validators=[validators.DataRequired()]
    )

    def validate(self):
        check_validate = super(RegisterForm, self).validate()
        if not check_validate:
            return False

        user = User.objects(username=self.username.data).first()
        if user:
            self.username.errors.append('Username already exists.')
            return False

        return True


class LoginForm(Form):
    username = TextField(
        'Username',
        validators=[validators.DataRequired()]
    )

    def validate(self):
        check_validate = super(LoginForm, self).validate()
        if not check_validate:
            return False

        user = User.objects(username=self.username.data).first()
        if not user:
            self.username.errors.append('Invalid username')
            return False

        return True
