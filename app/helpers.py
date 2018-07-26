from app import app
from flask import flash, redirect
from app.models import GeneralSetting, Trivia
from flask_login import current_user
from werkzeug import secure_filename
from wtforms.validators import ValidationError
import os

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