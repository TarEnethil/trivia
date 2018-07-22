from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from app import app, db
from app.trivia import bp
from app.helpers import page_title, redirect_non_admins
from app.trivia.forms import CategoryForm, TriviaForm
from app.models import User, Category, Trivia
from flask_login import current_user, login_required
from werkzeug import secure_filename
from datetime import datetime
import os

@bp.route("/")
@login_required
def index():
    lane1 = Trivia.query.filter(Trivia.lane==1)
    lane2 = Trivia.query.filter(Trivia.lane==2)
    lane3 = Trivia.query.filter(Trivia.lane==3).order_by(Trivia.lane_switch_ts).limit(5)

    return render_template("trivia/index.html", lane1=lane1, lane2=lane2, lane3=lane3, title=page_title("Trivia"))

@bp.route("/create", methods=["GET", "POST"])
@login_required
def create_trivia():
    redirect_non_admins()

    form = TriviaForm()

    form.lane.choices = [(1, "New"), (2, "Ongoing"), (3, "Published"), (4, "Cancelled")]

    categories = Category.query.all()

    cat_choices = []
    for cat in categories:
        cat_choices.append((cat.id, cat.name))

    form.category.choices = cat_choices

    if form.validate_on_submit():
        trivia = Trivia(title=form.title.data, description=form.description.data, category=form.category.data, lane=form.lane.data)
        db.session.add(trivia)
        db.session.commit()

        Flash("Trivia was created.")
        return redirect(url_for("trivia.index"))

    return render_template("trivia/trivia.html", form=form)

@bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_trivia(id):
    redirect_non_admins()

    form = TriviaForm()
    trivia = Trivia.query.get(id)

    form.lane.choices = [(1, "New"), (2, "Ongoing"), (3, "Published"), (4, "Cancelled")]

    categories = Category.query.all()

    cat_choices = []
    for cat in categories:
        cat_choices.append((cat.id, cat.name))

    form.category.choices = cat_choices

    if form.validate_on_submit():
        trivia.title = form.title.data
        trivia.description = form.description.data

        if trivia.lane != form.lane.data:
            trivia.lane_switch_ts = datetime.utcnow

        trivia.lane = form.lane.data
        trivia.category = form.category.data
        db.session.commit()

        flash("Trivia was edited")
        return redirect(url_for("trivia.index"))

    form.title.data = trivia.title
    form.description.data = trivia.description
    form.lane.data = trivia.lane
    form.category.data = trivia.category

    return render_template("trivia/trivia.html", form=form)

@bp.route("/publish/<int:id>", methods=["GET", "POST"])
@login_required
def publish_trivia(id):
    trivia = Trivia.query.get(id)

    trivia.lane = 3
    trivia.lane_switch_ts = datetime.utcnow

    flash("Trivia published.")
    db.session.commit()

    return render_template("trivia/trivia.html", form=form)

@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    redirect_non_admins()

    categories = Category.query.all()

    return render_template("trivia/settings.html", categories=categories, title=page_title("Categories"))

@bp.route("/category/create", methods=["GET", "POST"])
@login_required
def category_create():
    redirect_non_admins()

    form = CategoryForm()

    if form.validate_on_submit():
        new_cat = Category(name=form.name.data, color=form.color.data.hex)

        db.session.add(new_cat)
        db.session.commit()

        flash('"' + form.name.data + '" was successfully created.')
        return redirect(url_for('trivia.settings'))

    return render_template("trivia/category.html", form=form, title=page_title("Create category"))

@bp.route("/categorys/edit/<id>", methods=["GET", "POST"])
@login_required
def category_edit(id):
    redirect_non_admins()

    form = CategoryForm()
    category = Category.query.filter_by(id=id).first_or_404()

    if form.validate_on_submit():
        category.name = form.name.data
        category.color = form.color.data.hex

        db.session.commit()
        flash('"' + form.name.data + '" was successfully edited.')
        return redirect(url_for('trivia.settings'))

    form.name.data = category.name
    form.color.data = category.color
    return render_template("trivia/category.html", form=form, category=category, title=page_title("Edit category"))
