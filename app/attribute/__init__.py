from flask import Blueprint

attribute_bp = Blueprint(
    'attribute',
    __name__,
    template_folder='./templates'
)

from . import views
