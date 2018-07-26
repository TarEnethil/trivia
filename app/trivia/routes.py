from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from app import app, db
from app.trivia import bp
from app.helpers import page_title, redirect_non_admins, get_published_count, get_published_count_cat
from app.trivia.forms import CategoryForm, TriviaForm
from app.models import User, Category, Trivia, Lane
from flask_login import current_user, login_required
from werkzeug import secure_filename
from datetime import datetime
import os

@bp.route("/")
@login_required
def index():
    lane1 = Trivia.query.filter(Trivia.lane==1).order_by(Trivia.lane_switch_ts.desc())
    lane2 = Trivia.query.filter(Trivia.lane==2).order_by(Trivia.lane_switch_ts.desc())
    lane3 = Trivia.query.filter(Trivia.lane==3).order_by(Trivia.lane_switch_ts.desc()).limit(5)

    cq = Category.query.all()

    categories = {}

    for c in cq:
        categories[c.id] = { "color": c.color, "name": c.name }

    return render_template("trivia/index.html", lane1=lane1, lane2=lane2, lane3=lane3, categories=categories, title=page_title("Oppa kanban-style"))

@bp.route("/lane/<int:id>")
@login_required
def lane(id):
    lane_content = Trivia.query.filter(Trivia.lane==id).order_by(Trivia.lane_switch_ts.desc())
    lane_name = Lane.query.get(id).name

    cq = Category.query.all()

    categories = {}

    for c in cq:
        categories[c.id] = { "color": c.color, "name": c.name }

    return render_template("trivia/lane.html", lane_content=lane_content, categories=categories, lane_name=lane_name, title=page_title("Lane " + str(id)))

@bp.route("/create", methods=["GET", "POST"])
@login_required
def create_trivia():
    redirect_non_admins()

    form = TriviaForm()

    lq = Lane.query.all()

    lanes = []

    for lane in lq:
        lanes.append((lane.id, lane.name))

    form.lane.choices = lanes

    categories = Category.query.all()

    cat_choices = []
    for cat in categories:
        cat_choices.append((cat.id, cat.name))

    form.category.choices = cat_choices

    if form.validate_on_submit():
        trivia = Trivia(title=form.title.data, description=form.description.data, category=form.category.data, lane=form.lane.data, sent_by=form.sent_by.data)
        db.session.add(trivia)
        db.session.commit()

        flash("Trivia was created.")
        return redirect(url_for("trivia.index"))

    return render_template("trivia/trivia.html", form=form, title=page_title("Create new trivia"))

@bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_trivia(id):
    redirect_non_admins()

    form = TriviaForm()
    trivia = Trivia.query.get(id)

    lq = Lane.query.all()

    lanes = []

    for lane in lq:
        lanes.append((lane.id, lane.name))

    form.lane.choices = lanes

    categories = Category.query.all()

    cat_choices = []
    for cat in categories:
        cat_choices.append((cat.id, cat.name))

    form.category.choices = cat_choices

    if form.validate_on_submit():
        trivia.title = form.title.data
        trivia.description = form.description.data
        trivia.sent_by = form.sent_by.data

        published = False

        if trivia.lane != form.lane.data:
            trivia.lane_switch_ts = datetime.utcnow()

            if form.lane.data == 3:
                published = True

        trivia.lane = form.lane.data
        trivia.category = form.category.data
        db.session.commit()

        flash("Trivia was edited")
        if published:
            return redirect(url_for("trivia.lane_publish", id=trivia.id))

        return redirect(url_for("trivia.index"))

    form.title.data = trivia.title
    form.description.data = trivia.description
    form.lane.data = trivia.lane
    form.category.data = trivia.category
    form.sent_by.data = trivia.sent_by

    return render_template("trivia/trivia.html", form=form, title=page_title("Edit trivia"))

@bp.route("/ongoing/<int:id>", methods=["GET", "POST"])
@login_required
def lane_ongoing_trivia(id):
    trivia = Trivia.query.get(id)

    trivia.lane = 2
    trivia.lane_switch_ts = datetime.utcnow()

    flash("Trivia switched to lane ongoing.")
    db.session.commit()

    return redirect(url_for("trivia.index"))

@bp.route("/cancel/<int:id>", methods=["GET", "POST"])
@login_required
def lane_cancelled_trivia(id):
    trivia = Trivia.query.get(id)

    trivia.lane = 4
    trivia.lane_switch_ts = datetime.utcnow()

    flash("Trivia switched to lane cancelled.")
    db.session.commit()

    return redirect(url_for("trivia.index"))

@bp.route("/new/<int:id>", methods=["GET", "POST"])
@login_required
def lane_new_trivia(id):
    trivia = Trivia.query.get(id)

    trivia.lane = 1
    trivia.lane_switch_ts = datetime.utcnow()

    flash("Trivia switched to lane new.")
    db.session.commit()

    return redirect(url_for("trivia.index"))

@bp.route("/publish/<int:id>", methods=["GET", "POST"])
@login_required
def lane_publish_trivia(id):
    trivia = Trivia.query.get(id)

    trivia.lane = 3
    trivia.lane_switch_ts = datetime.utcnow()

    prepend = "Trivia #" + get_published_count()

    if trivia.category != 1:
        c = Category.query.get(trivia.category)
        prepend += ", " + c.abbr + " #" + get_published_count_cat(trivia.category)

    if trivia.sent_by:
        prepend += ", Fremdeinsendung von " + trivia.sent_by

    prepend += ":"

    trivia.description = prepend + trivia.description

    flash("Trivia published.")
    db.session.commit()

    return redirect(url_for("trivia.index"))

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
        new_cat = Category(name=form.name.data, color=form.color.data.hex, abbr=form.abbr.data)

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
        category.abbr = form.abbr.data

        db.session.commit()
        flash('"' + form.name.data + '" was successfully edited.')
        return redirect(url_for('trivia.settings'))

    form.name.data = category.name
    form.color.data = category.color
    form.abbr.data = category.abbr
    return render_template("trivia/category.html", form=form, category=category, title=page_title("Edit category"))

@bp.route("/api/latest", methods=["GET"])
def api_latest_trivia():
    trivia = Trivia.query.filter(Trivia.lane==3).order_by(Trivia.lane_switch_ts.desc()).first_or_404()
    return jsonify(trivia.to_dict())

@bp.route("/api/<int:no>", methods=["GET"])
def api_specific_trivia(no):
    trivia = Trivia.query.filter(Trivia.lane==3).order_by(Trivia.lane_switch_ts.asc()).offset(no-1).first_or_404()
    return jsonify(trivia.to_dict())
