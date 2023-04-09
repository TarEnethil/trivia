from flask import flash, redirect, current_app
from app.models import GeneralSetting, Trivia, Category
from datetime import datetime
from flask_login import current_user
from wtforms.validators import ValidationError
from random import choice, randint
import telebot
import os
from uuid import uuid4

def redirect_non_admins():
    if not current_user.has_admin_role():
        flash("Operation not permitted.")
        redirect(url_for("index"))

def page_title(dynamic_part=None):
    static_part = GeneralSetting.query.get(1).title

    if dynamic_part != None:
        return static_part + " - " + dynamic_part
    else:
        return static_part

def get_published_count():
    q = Trivia.query.filter(Trivia.lane == 3)
    # count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    # count = q.session.execute(count_q).scalar()
    return str(q.count())

def get_published_count_cat(cat_id):
    q = Trivia.query.filter(Trivia.lane == 3).filter(Trivia.category == cat_id)
    return str(q.count())

def get_ready_count():
    q = Trivia.query.filter(Trivia.lane == 2)

    return q.count()

def get_published(no):
    return Trivia.query.filter(Trivia.lane==3).order_by(Trivia.lane_switch_ts.asc()).offset(no-1).first_or_404()

def get_random_published_id():
    n = get_published_count()
    return randint(1, int(n))

def get_random_ready():
    q = Trivia.query.filter(Trivia.lane == 2)

    if q.count() == 0:
        return None
    else:
        return choice(q.all())

def get_bot_token():
    return GeneralSetting.query.get(1).bot_token

def gen_new_bot_token(db):
    g = GeneralSetting.query.get(1)

    g.bot_token = str(uuid4())

    db.session.commit()

def publish_trivia(db, id):
    trivia = Trivia.query.filter_by(id=id).first_or_404()

    trivia.lane = 3
    trivia.lane_switch_ts = datetime.utcnow()

    prepend = "Trivia #" + get_published_count()

    if trivia.category != 1:
        c = Category.query.get(trivia.category)
        prepend += ", " + c.abbr + " #" + get_published_count_cat(trivia.category)

    if trivia.sent_by:
        prepend += ", Fremdeinsendung von " + trivia.sent_by

    prepend += ": "

    trivia.description = prepend + trivia.description
    db.session.commit()

def send_to_owner(bot, msg):
    if bot == None or current_app.config["TELEGRAM_OWNER_CHAT_ID"] == None:
        return

    bot.send_message(current_app.config["TELEGRAM_OWNER_CHAT_ID"], msg)

def send_to_channel(bot, msg):
    if bot == None or current_app.config["TELEGRAM_CHANNEL_CHAT_ID"] == None:
        return

    bot.send_message(current_app.config["TELEGRAM_CHANNEL_CHAT_ID"], msg)

class LessThanOrEqual(object):
    def __init__(self, comp_value_field_name):
        self.comp_value_field_name = comp_value_field_name

    def __call__(self, form, field):
        other_field = form._fields.get(self.comp_value_field_name)

        if other_field is None:
            raise Exception('No field named %s in form' % self.comp_value_field_name)

        if other_field.data and field.data:
            if field.data > other_field.data:
                raise ValidationError("Value must be less than or equal to %s" % self.comp_value_field_name)

class GreaterThanOrEqual(object):
    def __init__(self, comp_value_field_name):
        self.comp_value_field_name = comp_value_field_name

    def __call__(self, form, field):
        other_field = form._fields.get(self.comp_value_field_name)

        if other_field is None:
            raise Exception('No field named %s in form' % self.comp_value_field_name)

        if other_field.data and field.data:
            if field.data < other_field.data:
                raise ValidationError("Value must be greater than or equal to %s" % self.comp_value_field_name)