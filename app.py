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
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
app.register_blueprint(auth_bp)

# Crear tablas
with app.app_context():
    db.create_all()

# Crear admin inicial al iniciar la app
with app.app_context():
    admin = User.query.filter_by(email="admin@starbite.local").first()
    if not admin:
        admin = User(
            email="admin@starbite.local",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()


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


@app.route("/add", methods=["GET", "POST"])
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
            telefono=telefono,
            plan=plan,
            costo=costo,
            fecha_pago=fecha_pago,
            estado="Pendiente"
        )

        db.session.add(c)
        db.session.commit()

        flash("Cliente agregado correctamente", "success")
        return redirect(url_for("index"))

    return render_template("add_client.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_client(id):
    c = Cliente.query.get_or_404(id)

    if request.method == "POST":
        c.nombre = request.form["nombre"]
        c.telefono = request.form["telefono"]
        c.plan = request.form["plan"]
        c.costo = float(request.form["costo"])
        c.fecha_pago = request.form["fecha_pago"]

        db.session.commit()

        flash("Cliente actualizado correctamente", "success")
        return redirect(url_for("index"))

    return render_template("edit_client.html", c=c)


@app.route("/delete/<int:id>")
@login_required
def delete_client(id):
    if current_user.role != "admin":
        flash("Solo administradores pueden eliminar clientes.", "danger")
        return redirect(url_for("index"))

    c = Cliente.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()

    flash("Cliente eliminado correctamente", "success")
    return redirect(url_for("index"))


@app.route("/change_state/<int:id>")
@login_required
def change_state(id):
    c = Cliente.query.get_or_404(id)
    estados = ["Pendiente", "Pagado", "Desconectado"]

    actual = c.estado
    nuevo = estados[(estados.index(actual) + 1) % len(estados)]
    c.estado = nuevo

    db.session.commit()

    flash("Estado actualizado", "info")
    return redirect(url_for("index"))


@app.route("/export")
@login_required
def exportar():
    clientes = Cliente.query.all()

    df = pd.DataFrame([{
        "Nombre": c.nombre,
        "Teléfono": c.telefono,
        "Plan": c.plan,
        "Costo": c.costo,
        "Fecha Pago": c.fecha_pago,
        "Estado": c.estado
    } for c in clientes])

    out = io.BytesIO()
    df.to_excel(out, index=False)
    out.seek(0)

    return send_file(out, download_name="clientes.xlsx", as_attachment=True)


@app.route("/import", methods=["POST"])
@login_required
def importar():
    archivo = request.files.get("file")

    if not archivo:
        flash("Selecciona un archivo .xlsx", "warning")
        return redirect(url_for("index"))

    df = pd.read_excel(archivo)

    for _, row in df.iterrows():
        c = Cliente(
            nombre=row.get("Nombre", ""),
            telefono=row.get("Teléfono", ""),
            plan=row.get("Plan", ""),
            costo=row.get("Costo", 0),
            fecha_pago=row.get("Fecha Pago", ""),
            estado=row.get("Estado", "Pendiente")
        )
        db.session.add(c)

    db.session.commit()

    flash("Clientes importados correctamente", "success")
    return redirect(url_for("index"))


@app.route("/reportes")
@login_required
def reportes():
    estados = ["Pagado", "Pendiente", "Desconectado"]
    totales = []

    for e in estados:
        total = db.session.query(func.sum(Cliente.costo)).filter(Cliente.estado == e).scalar() or 0
        totales.append(total)

    plt.bar(estados, totales)
    plt.title("Reporte financiero")
    plt.savefig("static/reporte.png")
    plt.clf()

    plt.pie(totales, labels=estados, autopct="%1.1f%%")
    plt.title("Distribución por estado")
    plt.savefig("static/pastel.png")
    plt.clf()

    return render_template("reportes.html")


@app.route("/recordatorios")
@login_required
def recordatorios():
    hoy = datetime.today()
    proximos = []

    clientes = Cliente.query.filter(Cliente.estado == "Pendiente").all()

    for c in clientes:
        try:
            fecha = datetime.strptime(c.fecha_pago, "%Y-%m-%d")
            if timedelta(days=-2) <= (fecha - hoy) <= timedelta(days=5):
                proximos.append(c)
        except:
            pass

    return render_template("recordatorios.html", clientes=proximos)


@app.route("/dashboard")
@login_required
def dashboard():
    total_clientes = Cliente.query.count()
    total_pagado = db.session.query(func.sum(Cliente.costo)).filter(Cliente.estado == "Pagado").scalar() or 0
    total_pendiente = db.session.query(func.sum(Cliente.costo)).filter(Cliente.estado == "Pendiente").scalar() or 0
    total_descon = db.session.query(func.sum(Cliente.costo)).filter(Cliente.estado == "Desconectado").scalar() or 0

    return render_template("dashboard.html",
                           total_clientes=total_clientes,
                           total_pagado=total_pagado,
                           total_pendiente=total_pendiente,
                           total_descon=total_descon)
