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
        _index = {}
        with open(pkg_resources.resource_filename('biometalib', 'data/flybase_example.yaml'), 'r') as fh:
            attrs = yaml.load(fh, Loader=yaml.RoundTripLoader)
            _attrs = []
            for name, syn in attrs.items():
                for v in syn:
                    _attrs.append({'name': v, 'synonym':  name})
                    _index[v] = len(_attrs) - 1

            AttributeSelector(user=current_user.username,
                              attributes=_attrs,
                              index=_index).save()

            return AttributeSelector.objects(user=current_user.username).first()
    else:
        return _user


def get_attr(name):
    """Helper to get queried attribute."""
    userDoc = get_user()
    _idx = userDoc.index.get(name, None)

    if _idx is not None:
        return userDoc.attributes[_idx]
    else:
        return None


def add_attr(name, synonym):
    """Add name:synonym pairs to user selected attributes.

    Helper function to add attributes to the current user's document.
    """
    # The AttributeSelector document for the current user.
    userDoc = get_user()

    # Attribute list for the current user
    userAttrs = userDoc.attributes
    index = userDoc.index

    _idx = index.get(name, None)

    if _idx is not None:
        userAttrs[_idx]['name'] = name
        userAttrs[_idx]['synonym'] = synonym
    else:
        userAttrs.append({'name': name, 'synonym': synonym})
        index[name] = len(userAttrs) - 1

    # If key not a current attribute then create
    userDoc.update(set__attributes=userAttrs, set__index=index)
    return


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
    # Build forms
    form = AttributeSelectorForm()
    pager = AttributePager()

    # Get session info or build list of attributes.
    session['attrIndex'] = session.get('attrIndex') or 0
    session['attrList'] = session.get('attrList') or get_all_attrs()

    # Get current attribute _type
    _currAttr = session['attrList'][session['attrIndex']]

    # Pre-populate the Rename form if there is already a value.
    if request.method == 'GET':
        _cv = get_attr(_currAttr)
        if _cv is not None:
            form['Rename'].default = _cv['synonym']
            form.process()

    if request.method == 'POST':
        # Adjust attribute types on form submit.
        if form.KeepButton.data:
            # Add attribute to the set
            add_attr(_currAttr, _currAttr)
        elif form.IgnoreButton.data:
            # Add the attribute to the ignore
            add_attr(_currAttr, 'Ignore')
        elif form.RenameButton.data and form.Rename.data and form.validate_on_submit():
            # Add the attribute to the renamed value
            add_attr(_currAttr, form.Rename.data)

        # Change current attribute type on pager submit
        if pager.Previous.data:
            # Decrement the index
            session['attrIndex'] = session['attrIndex'] - 1
            if session['attrIndex'] < 0:
                session['attrIndex'] = len(session['attrList']) + session['attrIndex']
            return redirect(url_for('.attribute_selector'))
        elif pager.Next.data:
            # Increment the index
            session['attrIndex'] = session['attrIndex'] + 1
            if session['attrIndex'] >= len(session['attrList']):
                session['attrIndex'] = session['attrIndex'] - len(session['attrList'])
            return redirect(url_for('.attribute_selector'))

        # Increment the index
        session['attrIndex'] = session['attrIndex'] + 1

        return redirect(url_for('.attribute_selector'))

    # Get information about the current attribute
    num_samples, num_projects, examples = get_examples(_currAttr)

    # Get information about the current user's list of attribute types. Also
    # get a list of ignored samples.
    user_attr = []
    ignored = []
    for x in get_user().attributes:
        _syn = x['synonym']
        if _syn == 'Ignore':
            ignored.append(x['name'])
        elif _syn not in user_attr:
            user_attr.append(_syn)


    # Get current attribute count
    num_attr = len(session['attrList'])
    curr_attr_num = session['attrIndex'] + 1

    return render_template('attribute.html', form=form, current_user=current_user,
                           attribute=_currAttr, number_attributes=num_attr,
                           current_attr_cnt=curr_attr_num, num_samples=num_samples,
                           num_projects=num_projects, examples=examples, user_attr=user_attr,
                           ignored=ignored, pager=pager)


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
