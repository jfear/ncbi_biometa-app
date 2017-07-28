import os
from collections import OrderedDict
from itertools import chain
import json
from flask import render_template, redirect, request, flash, url_for, current_app
from flask_login import current_user
from . import main_bp
from .forms import PerPageForm, QuerySampleAttribute, AttributeForm
from ..models import Biometa
from biometalib.models import CleanedAttributes
from biometalib.models import Biometa as Bm


columnMapping = OrderedDict([
    ('BioSample', '$_id'),
    ('BioProject', '$bioproject'),
    ('SRA Study', '$srs'),
    ('SRA Project', '$srp'),
    ('SRA Experiments', '$experiments.srx'),
    ('SRA Runs', '$experiments.runs'),
])


@main_bp.route("/", methods=["GET"])
@main_bp.route("/q?=<osearch>")
def home(osearch=''):
    """Playing with datatables."""
    return render_template('index.html', columns=columnMapping.keys(), osearch=osearch)


@main_bp.route("/<sample>", methods=["GET", "POST"])
def sample(sample):
    sample_data = Biometa.objects.get_or_404(pk=sample)
    form = AttributeForm()

    if (request.method == 'POST') and form.validate_on_submit():
        _data = {k: v for k, v in form.data.items() if (v != '') & (k != 'csrf_token') & (k != 'submit')}
        Biometa.objects(pk=sample).update_one(set__user_annotation={current_user.username: CleanedAttributes(**_data)})
        flash("Updated record.", "success")
        return render_template('sample.html', sample=sample_data, form=form)
    try:
        _data = sample_data.user_annotation[current_user.username].to_mongo().to_dict()
    except KeyError:
        _data = {}

    attrs = [x['name'] for x in sample_data.sample_attributes]
    for i in form:
        key = i.id
        if _data.get(key, ''):
            value = _data[key]
        elif key == 'sample_title':
            value = sample_data.sample_title
        elif key in attrs:
            value = [x['value'] for x in sample_data.sample_attributes if x['name'] == key][0]
        else:
            value = ''
        form[key].default = value
    form.process()

    return render_template('sample.html', sample=sample_data, form=form)


def join_list(ll):
    """Join a list of values.

    Joins a list of values with a |, and adds a line break every 4 items. Also
    flattens 2d lists.
    """
    # flatten if 2d list
    if isinstance(ll[0], list):
        flat = list(set(chain(*ll)))
    else:
        flat = ll

    # Join adding returns
    out = ''
    for i, value in enumerate(flat):
        if i == 0:
            out = str(value)
        elif i % 4 == 0:
            out += '|\n' + str(value)
        else:
            out += '|' + str(value)
    return out


@main_bp.route("/_dt", methods=["GET", "POST"])
def get_server_data():
    """Build the datatable."""
    pipeline = [{
            '$project': {
                '_id': 0,
                **columnMapping
            },
        },
        ]

    payload = []
    for record in Bm.objects.aggregate(*pipeline):
        # clean missing columns
        for key in columnMapping.keys():
            if key not in record:
                record[key] = ''

        # Add link to BioSample
        bs = record['BioSample']
        url = url_for("main.sample", sample=bs)
        record['BioSample'] = '<a href="{}">{}</a>'.format(url, bs)

        # Concatenat SRX and SRRs
        record['SRA Experiments'] = join_list(record['SRA Experiments'])
        record['SRA Runs'] = join_list(record['SRA Runs'])

        # Save record
        payload.append(record)

    return json.dumps({'data': payload})
