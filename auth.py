from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, LoginManager
from models import User, db

auth = Blueprint('auth', __name__)
login_manager = LoginManager()


# Cargar usuario por ID (Requerido por Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# LOGIN
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Credenciales incorrectas", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("index"))

    return render_template("login.html")


# REGISTER (no protegido)
@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user:
            flash("El usuario ya existe", "warning")
            return redirect(url_for("auth.register"))

        new_user = User(
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registro exitoso, ahora inicia sesión", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# LOGOUT
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
