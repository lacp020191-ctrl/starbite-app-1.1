from database import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="empleado")  # admin / empleado

class Cliente(db.Model):
    __tablename__ = "clientes"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(50))
    plan = db.Column(db.String(100))
    costo = db.Column(db.Float, default=0.0)
    fecha_pago = db.Column(db.String(20))
    estado = db.Column(db.String(20), default="Pendiente")
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
