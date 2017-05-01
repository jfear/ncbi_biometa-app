from flask import render_template, redirect, request, flash, url_for, current_app, jsonify
from . import sandbox_bp
from .forms import TestForm, TestFormTwo, PerPageForm
from ..models import Biometa


@sandbox_bp.route("/test", methods=["GET", "POST"])
def test():
    form = TestForm(request.form)
    return render_template('test.html', form=form)


@sandbox_bp.route("/autocomplete", methods=["GET"])
def autocomplete_abc():
    NAMES=["abc","abcd","abcde","abcdef"]
    search = request.args.get('term')
    current_app.logger.debug(search)
    return jsonify(json_list=NAMES)


@sandbox_bp.route("/test2", methods=["GET", "POST"])
def test2():
    form = TestFormTwo(request.form)
    return render_template('test2.html', form=form)


@sandbox_bp.route("/multi", methods=["GET", "POST"])
def multi():
    # Get any request information from the URL
    page = int(request.args.get('page', 1))
    per_pages = int(request.args.get('per_pages', 20))
    samples = request.args.get('samples', '').split(',')

    if isinstance(samples, str):
        samples = [samples]

    # Get the form
    form = PerPageForm(request.form)

    if request.method == 'POST':
        per_pages = int(form.per_pages.data)
    else:
        form.per_pages.default = per_pages
        form.process()

    paginated_table = Biometa.objects(pk__in=samples).order_by('biosample').paginate(page=page, per_page=per_pages)
    return render_template('multi.html', paginated_table=paginated_table, form=form)
