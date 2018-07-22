from flask import render_template, flash, redirect, url_for, request, jsonify
from app import db
from app.user import bp
from app.helpers import page_title, redirect_non_admins
from app.user.forms import CreateUserForm, EditProfileForm, EditProfileFormAdmin
from app.models import User, GeneralSetting
from flask_login import current_user, login_required
from datetime import datetime

@bp.route("/profile/<username>")
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    return render_template("user/profile.html", user=user, title=page_title("User profile"))

@bp.route("/edit/<username>", methods=["GET", "POST"])
@login_required
def edit(username):
    if current_user.has_admin_role() or current_user.username == username:

        if current_user.has_admin_role():
            form = EditProfileFormAdmin()
        else:
            form = EditProfileForm()

        user = User.query.filter_by(username=username).first_or_404()

        if form.validate_on_submit():
            user.about = form.about.data

            if(form.password.data):
                user.set_password(form.password.data)

                if current_user.username == user.username:
                    user.must_change_password = False
                elif current_user.has_admin_role():
                    # user must reset password after it has been changed by an admin
                    user.must_change_password = True

            db.session.commit()
            flash("Your changes have been saved.")

            return redirect(url_for("user.profile", username=username))
        elif request.method == "GET":
            form.about.data = user.about

        return render_template("user/edit.html", form=form, user=user, title=page_title("Edit profile"))
    else:
        flash("You dont have the neccessary role to perform this action.")
        return redirect(url_for("index"))

@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    redirect_non_admins()

    form = CreateUserForm()

    if form.validate_on_submit():
        new_user = User(username=form.username.data)
        new_user.set_password(form.password.data)

        new_user.created = datetime.utcnow()

        db.session.add(new_user)
        db.session.commit()

        flash("New user " + new_user.username + " created.")
        return redirect(url_for('user.list'))
    else:
        return render_template("user/create.html", form=form, title=page_title("Create new user"))

@bp.route("/list")
@login_required
def list():
    redirect_non_admins()

    users = User.query.all()

    return render_template("user/list.html", users=users, title=page_title("User list"))