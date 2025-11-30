from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import User
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user, LoginManager

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))

        flash("Correo o contraseña incorrectos", "danger")

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET","POST"])
@login_required
def register():
    if current_user.role != "admin":
        flash("Solo un administrador puede crear usuarios.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        if User.query.filter_by(email=email).first():
            flash("Este correo ya está registrado.", "warning")
            return redirect(url_for("auth.register"))

        hashed = generate_password_hash(password)
        u = User(email=email, password=hashed, role=role)
        db.session.add(u)
        db.session.commit()

        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
