import pkg_resources
from flask import render_template, session, redirect, request, flash, url_for, current_app, jsonify
from flask_login import current_user, login_required
from . import attribute_bp
from .forms import AttributeSelectorForm
from .models import AttributeSelector

from ruamel import yaml


def get_attrs():
    # Get the current users list of attributes
    attrs = AttributeSelector.objects(data=current_user.username)

    # Import the list of attributes from example YAML
    with open(pkg_resources('biometalib', 'data/flybase_example.yaml'), 'r') as fh:
        attrs = yaml.load(fh, Loader=yaml.RoundTripLoader)
        import pdb; pdb.set_trace()
        return attrs.keys()


@attribute_bp.route("/attribute", methods=["GET", "POST"])
@login_required
def attribute_selector():
    form = AttributeSelectorForm()
    return render_template('attribute.html', form=form, current_user=current_user)
#     if request.method == 'GET':
#         session['attrList'] = session.get('attrList', get_attrs())
#
#     if (request.method == 'POST'): #and query_form.search.data and query_form.validate_on_submit():
#
#     return render_template('attribute.html', form=form, current_user=current_user, payload=payload)
