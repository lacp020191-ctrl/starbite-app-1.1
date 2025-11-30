from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from config import Config
from database import db
from models import Cliente, User
from auth import auth_bp, login_manager
from flask_login import login_required, current_user
import pandas as pd
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
from sqlalchemy import func

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
app.register_blueprint(auth_bp)

# ============================================================
# Crear DB y admin inicial (compatible con Flask 3.x)
# ============================================================
with app.app_context():
    # Crear tablas
    db.create_all()

    # Crear admin inicial si no existe
    admin = User.query.filter_by(email="admin@starbite.local").first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin = User(
            email="admin@starbite.local",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

# ============================================================
# RUTAS
# ============================================================

@app.route("/")
@login_required
def index():
    q = request.args.get("q", "")
    query = Cliente.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            (Cliente.nombre.ilike(like)) |
            (Cliente.telefono.ilike(like)) |
            (Cliente.plan.ilike(like))
        )

    clientes = query.order_by(Cliente.id.desc()).all()
    return render_template("index.html", clientes=clientes, q=q)


@app.route("/add", methods=["GET","POST"])
@login_required
def add_client():
    if request.method == "POST":
        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        plan = request.form["plan"]
        costo = float(request.form["costo"])
        fecha_instalacion = request.form["fecha_instalacion"]

        fecha_pago = (
            datetime.strptime(fecha_instalacion, "%Y-%m-%d") + timedelta(days=30)
        ).strftime("%Y-%m-%d")

        c = Cliente(
            nombre=nombre,
