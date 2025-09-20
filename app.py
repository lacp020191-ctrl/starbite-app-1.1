
from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

app = Flask(__name__)
clientes = []

@app.route('/')
def index():
    return render_template('index.html', clientes=clientes)

@app.route('/agregar', methods=['POST'])
def agregar():
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    plan = request.form['plan']
    costo = float(request.form['costo'])
    fecha_instalacion = datetime.strptime(request.form['fecha_instalacion'], '%Y-%m-%d')
    fecha_pago = (fecha_instalacion + timedelta(days=30)).strftime('%Y-%m-%d')
    clientes.append({
        'nombre': nombre,
        'telefono': telefono,
        'plan': plan,
        'costo': costo,
        'fecha_pago': fecha_pago,
        'estado': 'Pendiente'
    })
    return redirect('/')

@app.route('/cambiar_estado/<int:id>')
def cambiar_estado(id):
    estados = ['Pendiente', 'Pagado', 'Desconectado']
    actual = clientes[id]['estado']
    nuevo = estados[(estados.index(actual)+1)%3]
    clientes[id]['estado'] = nuevo
    return redirect('/')

@app.route('/eliminar/<int:id>')
def eliminar(id):
    clientes.pop(id)
    return redirect('/')

@app.route('/exportar')
def exportar():
    df = pd.DataFrame(clientes)
    df.to_excel("clientes.xlsx", index=False)
    return send_file("clientes.xlsx", as_attachment=True)

@app.route('/reportes')
def reportes():
    estados = ['Pagado', 'Pendiente', 'Desconectado']
    totales = [sum(c['costo'] for c in clientes if c['estado']==e) for e in estados]
    plt.bar(estados, totales, color=['green','orange','red'])
    plt.title("Reporte financiero")
    plt.ylabel("Monto total")
    plt.savefig("reporte.png")
    plt.clf()
    plt.pie(totales, labels=estados, autopct='%1.1f%%')
    plt.title("Distribución de estados")
    plt.savefig("pastel.png")
    return '''
    <h2>📊 Reportes financieros</h2>
    <img src="/static/reporte.png" width="400"><br><br>
    <img src="/static/pastel.png" width="400"><br><br>
    <a href="/">← Volver</a>
    '''

@app.route('/recordatorios')
def recordatorios():
    hoy = datetime.today()
    lista = []
    for c in clientes:
        fecha = datetime.strptime(c['fecha_pago'], '%Y-%m-%d')
        if c['estado'] == 'Pendiente' and fecha - hoy <= timedelta(days=3) and fecha - hoy >= timedelta(days=-2):
            lista.append(c)
    html = "<h2>🔔 Recordatorios automáticos</h2><ul>"
    for c in lista:
        mensaje = f"Hola {c['nombre']}, tu pago de ${c['costo']} por el plan {c['plan']} vence el {c['fecha_pago']}. Gracias por confiar en StarBite."
        enlace = f"https://wa.me/52{c['telefono']}?text={mensaje.replace(' ', '%20')}"
        html += f"<li>{c['nombre']} - <a href='{enlace}' target='_blank'>Enviar WhatsApp</a></li>"
    html += "</ul><a href='/'>← Volver</a>"
    return html

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0",port=port)
