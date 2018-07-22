from app import app, db
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from app.helpers import LessThanOrEqual, GreaterThanOrEqual
from wtforms import StringField, TextAreaField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, InputRequired, NumberRange
from wtforms_components import ColorField

class CategoryForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=64)])
    color = ColorField("Color")

    submit = SubmitField("submit")

class TriviaForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    description = TextAreaField("Description", render_kw={"rows": 15})

    lane = SelectField("Lane", coerce=int)
    category = SelectField("Category", coerce=int)

    submit = SubmitField("submit")