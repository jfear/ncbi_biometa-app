from flask import render_template, redirect, request, flash, url_for, current_app, jsonify
from . import main_bp
from .forms import PerPageForm
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
    sample = Biometa.objects.get_or_404(pk=sample)
    return render_template('sample.html', sample=sample)
