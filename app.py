from flask import Flask, render_template
from flask_login import login_required
from models import db
from auth import auth, login_manager

app = Flask(__name__)
app.config.from_object("config.Config")

db.init_app(app)

login_manager.init_app(app)
login_manager.login_view = "auth.login"

app.register_blueprint(auth)


# ------------------------------
# RUTA PRINCIPAL
# ------------------------------
@app.route("/")
@login_required
def index():
    return render_template("index.html")


# ------------------------------
# RUTAS QUE FALTABAN (TEMPORALES)
# ------------------------------
@app.route("/recordatorios")
@login_required
def recordatorios():
    return render_template("recordatorios.html")


@app.route("/reportes")
@login_required
def reportes():
    return render_template("reportes.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")
