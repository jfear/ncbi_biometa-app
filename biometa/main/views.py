from flask import render_template, redirect, request, flash, url_for, current_app
from . import main_bp
from .forms import PerPageForm, TestForm
from ..models import Biometa


@main_bp.route("/", methods=["GET", "POST"])
def home():
    # Get any request information from the URL
    page = int(request.args.get('page', 1))
    per_pages = int(request.args.get('per_pages', 20))

    # Get the form
    form = PerPageForm(request.form)

    if request.method == 'POST':
        per_pages = int(form.per_pages.data)
    else:
        form.per_pages.default = per_pages
        form.process()

    paginated_table = Biometa.objects.order_by('biosample').paginate(page=page, per_page=per_pages)
    return render_template('index.html', paginated_table=paginated_table, form=form)

@main_bp.route("/<sample>", methods=["GET", "POST"])
def sample(sample):
    sample = Biometa.objects.get_or_404(biosample=sample)
    return render_template('sample.html', sample=sample)


@main_bp.route("/test", methods=["GET", "POST"])
def test():
    form = TestForm(request.form)
    return render_template('test.html', form=form)

from flask import jsonify
NAMES=["abc","abcd","abcde","abcdef"]

@main_bp.route("/autocomplete", methods=["GET"])
def autocomplete():
    search = request.args.get('term')
    current_app.logger.debug(search)
    return jsonify(json_list=NAMES)
