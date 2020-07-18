from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from app import app, db, bot
from app.trivia import bp
from app.helpers import page_title, redirect_non_admins, get_published_count, get_published_count_cat, publish_trivia, get_random_ready, send_to_owner, send_to_channel, get_ready_count, get_bot_token, gen_new_bot_token, get_random_published_id, get_published
from app.trivia.forms import CategoryForm, TriviaForm
from app.forms import SettingsForm
from app.models import User, Category, Trivia, Lane, GeneralSetting
from flask_login import current_user, login_required
from werkzeug import secure_filename
from datetime import datetime
from random import randint
import telebot
import os
import re

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

    lq = Lane.query.filter(Lane.id != 3)

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

@bp.route("/ready/<int:id>", methods=["GET", "POST"])
@login_required
def lane_ready_trivia(id):
    trivia = Trivia.query.get(id)

    trivia.lane = 2
    trivia.lane_switch_ts = datetime.utcnow()

    flash("Trivia switched to lane ready.")
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
    publish_trivia(id)

    flash("Trivia published.")

    return redirect(url_for("trivia.index"))

@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    redirect_non_admins()

    form = SettingsForm()
    settings = GeneralSetting.query.get(1)

    if form.validate_on_submit():
        settings.title = form.title.data

        flash("Settings changed.")

        db.session.commit()
    else:
        form.title.data = settings.title

    categories = Category.query.all()

    return render_template("trivia/settings.html", form=form, categories=categories, title=page_title("Categories"))

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

@bp.route("/bot/publish", methods=["GET"])
def bot_publish():
    if bot != None:
        url_token = request.args.get('token')
        our_token = get_bot_token()

        if url_token == None or url_token != our_token:
            return jsonify({"success": False}), 403

        t = get_random_ready()

        if t == None:
            send_to_owner("I was triggered to send a trivia, but there was none left!")
            return jsonify({"success": False}), 503

        publish_trivia(t.id)

        send_to_channel(t.description + "\n\nSent by @ThorstensTriviaBot")

        msg_to_owner = ""

        if app.config["TELEGRAM_ALWAYS_REPORT"]:
            msg_to_owner = "I just posted the Trivia '{}' to the channel.\n".format(t.title)

        ready = get_ready_count()

        warn = app.config["TELEGRAM_WARN_COUNT"]
        if warn and ready < warn:
            msg_to_owner += "Warning: "

        if app.config["TELEGRAM_ALWAYS_REPORT"] or (warn and ready < warn):
            msg_to_owner += "There are {} trivia left in the 'ready' lane.".format(ready)

        if msg_to_owner != "":
            send_to_owner(msg_to_owner)

        gen_new_bot_token()
        return jsonify({"success": True}), 200

if app.config["TELEGRAM_WEBHOOK_HOST"] != None:
    @bp.route("/bot/update/%s".format(app.config["TELEGRAM_TOKEN"]), methods=["POST"])
    def webhook():
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            flask.abort(403)

rgx = re.compile("/trivia (\d+)")

def log_message(message):
    if app.config["TELEGRAM_BOT_LOG"] == None or app.config["TELEGRAM_BOT_LOG"] == False:
        return

    if message.from_user.username:
        user = message.from_user.username
    else:
        user = message.from_user.first_name

    print("{}: {} sent message '{}'".format(datetime.fromtimestamp(message.date), user, message.text))

if bot != None:
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        log_message(message)
        msg = "Hello @{}!\n\n".format(message.from_user.username)
        msg += "I am @ThorstensTriviaBot (WIP). I currently support the following commands:\n\n"
        msg += "/random, /trivia\n"
        msg += "        get a random published fact\n"
        msg += "/trivia <number>\n"
        msg += "        get published trivia #<number>"
        msg += "\n\nThere are currently {} published facts.\n".format(get_published_count())
        msg += "If you find any bugs, feel free to report them to @TriviaThorsten or at https://tarenethil.github.com/trivia/issues"

        if app.config["TELEGRAM_BOT_LOG"] == True:
            msg += "\n\nNote: For debugging purposes, all messages are currently logged."

        bot.send_message(message.chat.id, msg)

    @bot.message_handler(commands=['random'])
    def random_trivia(message):
        log_message(message)
        t = get_published(get_random_published_id())

        bot.send_message(message.chat.id, t.description)

    @bot.message_handler(commands=['trivia'])
    def trivia(message):
        log_message(message)
        if message.text == "/trivia":
            random_trivia(message)
            return

        m = rgx.match(message.text)

        if m == None:
            bot.reply_to(message, "I could not extract a valid fact id from your query.")
            return

        try:
            tid = int(m.group(1))
        except:
            bot.reply_to(message, "I could not extract valid fact id from your query (target was {}).".format(m.group(1)))
            return

        if tid <= 0:
            bot.reply_to(message, "{} is not a valid fact id.".format(tid))
            return

        t = Trivia.query.filter(Trivia.lane==3).order_by(Trivia.lane_switch_ts.asc()).offset(tid-1).first()

        if t == None:
            bot.reply_to(message, "Sorry, I could not find the fact with id {}.".format(tid))
            return

        bot.send_message(message.chat.id, t.description)

    @bot.message_handler(func=lambda m: True)
    def default(message):
        log_message(message)

@bp.route("/api/", methods=["GET"])
def api_index():
    return redirect(url_for("trivia.api_latest_trivia"), code=302)

@bp.route("/api/latest", methods=["GET"])
def api_latest_trivia():
    trivia = Trivia.query.filter(Trivia.lane==3).order_by(Trivia.lane_switch_ts.desc()).first_or_404()
    resp = jsonify(trivia.to_dict())
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@bp.route("/api/<int:no>", methods=["GET"])
def api_specific_trivia(no):
    trivia = get_published(no)
    resp = jsonify(trivia.to_dict())
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@bp.route("/api/random", methods=["GET"])
def api_random_trivia():
    n = get_random_published_id()
    return redirect(url_for("trivia.api_specific_trivia", no=n))