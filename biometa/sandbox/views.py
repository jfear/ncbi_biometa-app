from flask import render_template, redirect, request, flash, url_for, current_app, jsonify
from . import sandbox_bp
from .forms import TestForm, TestFormTwo
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
