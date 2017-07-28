import pkg_resources
import json
import time
from collections import Counter

from flask import render_template, session, redirect, request, flash, url_for, current_app, jsonify
from flask_login import current_user, login_required

from ruamel import yaml

from biometalib.models import Biometa

from . import attribute_bp
from .forms import AttributeSelectorForm, AttributePager
from .models import AttributeSelector


def get_all_attrs():
    """Grab all attribute types from the Biometa database.

    Returns
    -------
    list
        sorted list containing all attribute types from the database.
    """
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

    Returns
    -------
    list of .models.AttributeValue
        Returns a list of AttributeValue objects. Using a list to help maintain
        order of attributes.
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
    """Get list of attributes already categorized by the current user.

    Returns
    -------
    list
        A list of attributes already categorized by the current user.
    """
    userAttrs = get_user()
    _attr = []
    for doc in userAttrs.attributes:
        for syn in doc.synonyms:
            _attr.append(syn)
    return _attr


def filter_attribute_list():
    """Filter out attributes already categorized by the current user.

    Returns
    -------
    list
        Reversed list of attributes not already categorized by the current user.
    """
    all_attrs = get_all_attrs()
    user_attrs = get_user_attrs()
    _attrs = []
    for x in all_attrs:
        if x not in user_attrs:
            _attrs.append(x)
    return _attrs[::-1]


def add_attr(key, value):
    """Add key:value pairs to user selected attributes.

    Helper function to add attributes to the current user's document.
    """
    # The AttributeSelector document for the current user.
    userDoc = get_user()

    # Attribute list for the current user
    userAttrs = userDoc.attributes

    # Remove value if already a top level attribute type.
    userAttrs = [x for x in userAttrs if x.name != value]

    # Remove value if already a synonym.
    _userAttrs = []
    for _attr in userAttrs:
        _attr.synonyms = [x for x in _attr.synonyms if x != value]
        _userAttrs.append(_attr)

    userAttrs = _userAttrs

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


def get_index(name, docs, field='name'):
    """Get index from list of dicts.

    Given a list of dicts, figure out the index that contains the value in the
    corresponding field.

    Returns
    -------
    int or None
        Retruns the index a value belongs to, or None
    """
    for i, doc in enumerate(docs):
        if doc[field] == name:
            return i
    return None


def get_examples(currAttr):
    """Get a list of current values.

    Given an attribute, pull out all of the values in that attribute column
    from the database. Also calculate basic information about the attribute
    use.

    Returns
    -------
    int
        Number of BioSamples that have this attribute type
    int
        Number of BioProjects that have this attribute type
    list
        List of values that correspond to this attribute type
    """
    num_samples = len(list(Biometa.objects.aggregate(*[
        {'$unwind': '$sample_attributes'},
        {'$match': {'sample_attributes.name': currAttr}},
    ])))

    # Count the number of projects that used attribute
    num_projects = len(list(Biometa.objects.aggregate(*[
        {'$unwind': '$sample_attributes'},
        {'$match': {'sample_attributes.name': currAttr}},
        {'$group': {'_id': '$bioproject'}},
    ])))

    # Get a list of all values from the attribute
    values = Biometa.objects.aggregate(*[
        {'$unwind': '$sample_attributes'},
        {'$match': {'sample_attributes.name': currAttr}},
        {
            '$project': {'_id': '$sample_attributes.value'}
        }
    ])

    # Count the number of times each value is present
    examples = Counter([x['_id'] for x in values])

    return num_samples, num_projects, sorted(examples.items(), key=lambda x: x[0])


@attribute_bp.route("/attribute", methods=["GET", "POST"])
@login_required
def attribute_selector():
    """Run the attribute selector.

    Originally designed as a CLI, attribute selector is a way to look at all
    attribute types and decide if you want to keep, ignore, or rename. This
    page will iterate over all attribute types in the database and get user
    input about how to handle the type.
    """
    form = AttributeSelectorForm()
    pager = AttributePager()

    session['attrIndex'] = session.get('attrIndex') or 0
    session['attrList'] = session.get('attrList') or get_all_attrs()
    _currAttr = session['attrList'][session['attrIndex']]

    if request.method == 'POST':
        if form.KeepButton.data:
            # Add attribute to the set
            add_attr(_currAttr, _currAttr)
        elif form.IgnoreButton.data:
            # Add the attribute to the ignore
            add_attr('Ignore', _currAttr)
        elif form.RenameButton.data and form.Rename.data and form.validate_on_submit():
            # Add the attribute to the renamed value
            add_attr(form.Rename.data, _currAttr)

        if pager.Previous.data:
            # Decrement the index
            session['attrIndex'] = session['attrIndex'] - 1
            return redirect(url_for('.attribute_selector'))
        elif pager.Next.data:
            # Increment the index
            session['attrIndex'] = session['attrIndex'] + 1
            return redirect(url_for('.attribute_selector'))

        # Increment the index
        session['attrIndex'] = session['attrIndex'] + 1

        return redirect(url_for('.attribute_selector'))

    # Get information about the current attribute
    num_samples, num_projects, examples = get_examples(_currAttr)

    # Get information about the current user's list of attribute types
    user_attr = [x['name'] for x in get_user().attributes]

    return render_template('attribute.html', form=form, current_user=current_user,
                           attribute=_currAttr, current_index=session['attrIndex'], num_samples=num_samples,
                           num_projects=num_projects, examples=examples, user_attr=user_attr, pager=pager)


@attribute_bp.route("/attributeMap", methods=["GET",])
def attribute_map():
    """Summary page of attribute type classification.

    It may be useful to look at all of the attributes and see how other users
    have classified them. This is a simple summary page where usernames are
    placed next to the attribute type. Top level attributes are the user's
    naming designation, while sub attributes are to be renamed to the top level
    attribute type.

    All of this code is data munging. The database is organized by user at the
    top level, I need attribute at the top level and then a list of users that
    have that attribute.
    """
    attrDict = json.loads(AttributeSelector.objects.to_json())

    # Make a new list to hold the re-organizedata.
    attrs = []
    # Iterate over each user
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
