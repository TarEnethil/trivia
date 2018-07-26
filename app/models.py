from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about = db.Column(db.String(1000))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    must_change_password = db.Column(db.Boolean, default=True)

    def has_admin_role(self):
        return self.id == 1

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class GeneralSetting(db.Model):
    __tablename__ = "general_settings"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    abbr = db.Column(db.String(10))
    color = db.Column(db.String(10))

class Lane(db.Model):
    __tablename__ = "lanes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))

class Trivia(db.Model):
    __tablename__ = "trivias"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(5000))
    sent_by = db.Column(db.String(64))
    lane_switch_ts = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.Integer, db.ForeignKey("users.id"))
    lane = db.Column(db.Integer, db.ForeignKey("lanes.id"), default=1)

    def category_color(self):
        return Category.query.get(self.category).color

    def category_name(self):
        return Category.query.get(self.category).name

    def is_lane(self, id):
        return self.lane == id

    def is_new_lane(self):
        return self.is_lane(1)

    def is_ongoing_lane(self):
        return self.is_lane(2)

    def is_published_lane(self):
        return self.is_lane(3)

    def is_cancelled_lane(self):
        return self.is_lane(4)

    def to_dict(self):
        data = {
            'fact' : self.description,
            'category' : self.category_name()
        }

        return data

@login.user_loader
def load_user(id):
    return User.query.get(int(id))