from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from app import app, db
from app.helpers import page_title, redirect_non_admins
from app.forms import LoginForm, SettingsForm, InstallForm
from app.models import User, GeneralSetting, Lane
from flask_login import current_user, login_user, login_required, logout_user
from datetime import datetime
from werkzeug.urls import url_parse

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

        url = url_for("user.edit", username=current_user.username)
        if current_user.must_change_password and request.path != url:
            flash("You must change your password before proceeding")
            return redirect(url)

@app.route("/")
@app.route("/index")
@login_required
def index():
    return redirect(url_for("trivia.index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(request.full_path)
        else:
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')

            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for("index")

            return redirect(next_page)

    return render_template("login.html", title=page_title("Login"), form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/settings", methods=["GET", "POST"])
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

    return render_template("settings.html", form=form, title=page_title("General settings"))

@app.route("/__install__", methods=["GET", "POST"])
def install():
    if not GeneralSetting.query.get(1):
        form = InstallForm()

        if form.validate_on_submit():
            setting = GeneralSetting(title="My Page")
            db.session.add(setting)

            lane1 = Lane(name="New")
            lane2 = Lane(name="Ongoing")
            lane3 = Lane(name="Published")
            lane4 = Lane(name="Cancelled")

            db.session.add(lane1)
            db.session.add(lane2)
            db.session.add(lane3)
            db.session.add(lane4)

            admin = User(username=form.admin_name.data)
            admin.set_password(form.admin_password.data)
            admin.must_change_password = False

            db.session.add(admin)

            db.session.commit()

            flash("Install successful. You can now log in and check the settings.")

            return redirect(url_for("index"))

        return render_template("install.html", form=form, title="Install")
    else:
        flash("Setup was already executed.")
        return redirect(url_for("index"))

@app.route("/static_files/<path:filename>")
def static_files(filename):
    return send_from_directory(app.config["STATIC_DIR"], filename)