import json
from flask import render_template, redirect, request, flash, url_for, current_app
from flask_login import current_user
from . import main_bp
from .forms import PerPageForm, QuerySampleAttribute, AttributeForm
from ..models import Biometa
from biometalib.models import CleanedAttributes
from biometalib.models import Biometa as Bm


@main_bp.route("/", methods=["GET", "POST"])
def home():
    """Home page which contains a table with a list of samples."""

    # Get any request information from the URL
    page = int(request.args.get('page', 1))
    payload = {
        'per_pages': int(request.args.get('per_pages', 20)),
        'srr': request.args.get('srr', ''),
        'srx': request.args.get('srx', ''),
        'srp': request.args.get('srp', ''),
        'query': request.args.get('query', ''),
    }

    # Pull in search form.
    query_form = QuerySampleAttribute()
    if (request.method == 'POST') and query_form.search.data and query_form.validate_on_submit():
        payload['srr'] = query_form['SRR'].data
        payload['srx'] = query_form['SRX'].data
        payload['srp'] = query_form['SRP'].data
        payload['query'] = query_form['Attributes'].data
        return redirect(url_for("main.home", **payload))

    if payload['srr']:
        cursor = Biometa.objects(experiments__runs__icontains=payload['srr'])
    elif payload['srx']:
        cursor = Biometa.objects(experiments__srx=payload['srx'])
    elif payload['srp']:
        cursor = Biometa.objects(srp=payload['srp'])
    elif payload['query']:
        cursor = Biometa.objects(sample_attributes__value__icontains=payload['query'])
    else:
        cursor = Biometa.objects()

    # If there is only one item then send to the item page.
    if cursor.count() == 1:
        bio = cursor[0]
        return redirect(url_for("main.sample", sample=bio.biosample))

    # Pull in pagination form
    form = PerPageForm()

    if (request.method == 'POST') and form.submit.data:
        payload['per_pages'] = int(form.per_pages.data)
        return redirect(url_for("main.home", **payload))
    else:
        form.per_pages.default = payload['per_pages']
        form.process()

    paginated_table = cursor.order_by('biosample').paginate(page=page, per_page=payload['per_pages'])
    return render_template('index.html', paginated_table=paginated_table, form=form, query=query_form, current_user=current_user, payload=payload)

@main_bp.route("/<sample>", methods=["GET", "POST"])
def sample(sample):
    sample_data = Biometa.objects.get_or_404(pk=sample)
    form = AttributeForm()

    if (request.method == 'POST') and form.validate_on_submit():
        _data = {k: v for k, v in form.data.items() if (v != '') & (k != 'csrf_token')& (k != 'submit')}
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

@main_bp.route("/dt", methods=["GET", "POST"])
def dt():
    """Playing with datatables."""
    return render_template('index2.html')

@main_bp.route("/_dt", methods=["GET", "POST"])
def get_server_data():
    """Playing with datatables."""
    pipeline = [{
            '$project': {
                '_id': 0,
                'BioSample': '$_id',
                'BioProject': '$bioproject',
                'SRA Study': '$srs',
                'SRA Project': '$srp',
                'SRA Experiments': {
                    '$reduce': {
                        'input': '$experiments.srx',
                        'initialValue': '',
                        'in': { '$concat': ['$$value', '|', '$$this'] }
                    }
                },
            },
        },
        ]

    return json.dumps({'data': list(Bm.objects.aggregate(*pipeline))})

