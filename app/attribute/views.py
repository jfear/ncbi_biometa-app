import pkg_resources
import json
import time

from flask import render_template, session, redirect, request, flash, url_for, current_app, jsonify
from flask_login import current_user, login_required

from ruamel import yaml

from biometalib.models import Biometa

from . import attribute_bp
from .forms import AttributeSelectorForm
from .models import AttributeSelector


def get_all_attrs():
    """Grab all attribute types from the Biometa database."""
    cursor = Biometa.objects.aggregate(*[
        {'$unwind': '$sample_attributes'},
        {
            '$project': {'_id': '$sample_attributes.name'}
        }
    ])

    return sorted(list(set([x['_id'] for x in cursor])))


def get_user():
    """Look up the current users AttributeSelection document.

    If this document is empty then initialize with flybase_example.
    """
    _user = AttributeSelector.objects(user=current_user.username).first()
    if _user is None:
        with open(pkg_resources.resource_filename('biometalib', 'data/flybase_example.yaml'), 'r') as fh:
            attrs = yaml.load(fh, Loader=yaml.RoundTripLoader)
            AttributeSelector(user=current_user.username, attributes=[{'name': k, 'synonyms': v} for k, v in attrs.items()]).save()
            return AttributeSelector.objects(user=current_user.username).first()
    else:
        return _user


def get_user_attrs():
    """Get dictionary of attribute types mapped to user selected attribute types."""
    userAttrs = get_user()
    _attr = []
    for doc in userAttrs.attributes:
        for syn in doc.synonyms:
            _attr.append(syn)
    return _attr


def filter_attribute_list():
    """Filter out attributes that are already in user attributes."""
    all_attrs = get_all_attrs()
    user_attrs = get_user_attrs()
    _attrs = []
    for x in all_attrs:
        if x not in user_attrs:
            _attrs.append(x)
    return _attrs[::-1]


def add_attr(key, value):
    """Add key:value pairs to user selected attributes."""
    # The AttributeSelector document for the current user.
    userDoc = get_user()

    # Attribute list for the current user
    userAttrs = userDoc.attributes

    # Iterate over user attributes and append value if key matches attribute name
    for attr in userAttrs:
        if attr.name == key:
            if value not in attr.synonyms:
                attr.synonyms.append(value)
                userDoc.update(set__attributes=userAttrs)
            return

    # If key not a current attribute then create
    userAttrs.append({'name': key, 'synonyms': [value]})
    userDoc.update(set__attributes=userAttrs)
    return


@attribute_bp.route("/attribute", methods=["GET", "POST"])
@login_required
def attribute_selector():
    form = AttributeSelectorForm()

    # On GET pull session data
    if request.method == 'GET':
        # Get a list of attribute types
        pass
    session['attrList'] = session.get('attrList', filter_attribute_list())
    try:
        session['currAttr'] = session.get('currAttr', session['attrList'].pop())
    except IndexError:
        return redirect(url_for('.attribute_map'))

    if request.method == 'POST':
        currAttr = session['currAttr']
        if form.KeepButton.data:
            # Add attribute to the set
            add_attr(currAttr, currAttr)
        elif form.IgnoreButton.data:
            # Add the attribute to the ignore
            add_attr('Ignore', currAttr)
        elif form.RenameButton.data and form.Rename.data and form.validate_on_submit():
            # Add the attribute to the renamed value
            add_attr(form.Rename.data, currAttr)

        try:
            session['currAttr'] = session['attrList'].pop()
            return redirect(url_for('.attribute_selector'))
        except IndexError:
            return redirect(url_for('.attribute_map'))

    return render_template('attribute.html', form=form, current_user=current_user, attribute=session['currAttr'])


def get_index(name, docs, field='name'):
    """Get index from list of dicts.

    Given a list of dicts, figure out the index that contains the value.
    """
    for i, doc in enumerate(docs):
        if doc[field] == name:
            return i
    return None

@attribute_bp.route("/attributeMap", methods=["GET",])
def attribute_map():
    attrDict = json.loads(AttributeSelector.objects.to_json())
    attrs = []
    for user in attrDict:
        username = user['_id']
        for _attr in user['attributes']:
            _name = _attr['name']
            _syn = _attr['synonyms']
            _idx = get_index(_name, attrs)
            if _idx is None:
                _doc = {'name': _name, 'users': [username, ], 'synonyms': []}
                for n in _syn:
                    _doc['synonyms'].append({'name': n, 'users': [username, ]})
                attrs.append(_doc)
            else:
                _doc = attrs[_idx]
                _doc['users'].append(username)
                for s in _syn:
                    _i = get_index(s, _doc['synonyms'])
                    if _i is not None:
                        _doc['synonyms'][_i]['users'].append(username)
                    else:
                        _doc['synonyms'].append({'name': s, 'users': [username, ]})

    return render_template('attribute_map.html', attributes=attrs)
