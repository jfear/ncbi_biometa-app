from flask import Blueprint

main_bp = Blueprint(
    'attribute',
    __name__,
    template_folder='./templates'
)

from . import views
