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


def get_other_users():
    oUsers = []
    for oAttr in AttributeSelector.objects():
        if oAttr.user != current_user.username:
            oUsers.append(oAttr)
    return oUsers


def get_other_users_thoughts(currAttr):
    oUsers = get_other_users()
    thoughts = []
    for ouser in oUsers:
        if currAttr in ouser.index:
            user = ouser.user
            syn = ouser.attributes[ouser.index[currAttr]]['synonym']
            thoughts.append((user, syn))
    return thoughts


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
    examples = Counter([x['_id'] for x in values if '_id' in x])

    return num_samples, num_projects, sorted(examples.items(), key=lambda x: x[0])


def decrement_index():
    session['attrIndex'] = session['attrIndex'] - 1
    if session['attrIndex'] < 0:
        session['attrIndex'] = len(session['attrList']) + session['attrIndex']


def increment_index():
    session['attrIndex'] = session['attrIndex'] + 1
    if session['attrIndex'] >= len(session['attrList']):
        session['attrIndex'] = session['attrIndex'] - len(session['attrList'])


@attribute_bp.route("/attribute", methods=["GET", "POST"])
@attribute_bp.route("/attribute/<term>", methods=["GET"])
@login_required
def attribute_selector(term=None):
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

        if term is not None:
            try:
                session['attrIndex'] = session['attrList'].index(term)
                return redirect(url_for('.attribute_selector'))
            except ValueError:
                flash("There is no attribute with that name", "fail")
                return redirect(url_for('.attribute_selector'))

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
        elif form.SearchButton.data and form.Search.data and form.validate_on_submit():
            try:
                session['attrIndex'] = session['attrList'].index(form.Search.data)
                return redirect(url_for('.attribute_selector'))
            except ValueError:
                flash("There is no attribute with that name", "fail")
                return redirect(url_for('.attribute_selector'))

        # Change current attribute type on pager submit
        if pager.Previous.data:
            # Decrement the index
            decrement_index()
            return redirect(url_for('.attribute_selector'))
        elif pager.Next.data:
            # Increment the index
            increment_index()
            return redirect(url_for('.attribute_selector'))

        # Increment the index
        increment_index()
        return redirect(url_for('.attribute_selector'))

    # Get information about the current attribute
    num_samples, num_projects, examples = get_examples(_currAttr)

    # Get what other users say the current attribute should be
    other_users = get_other_users_thoughts(_currAttr)

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
                           ignored=ignored, pager=pager, thoughts=other_users)
