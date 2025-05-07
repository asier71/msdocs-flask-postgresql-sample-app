import os
from datetime import datetime
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# === CONFIGURACIÓN DE FLASK ===
app = Flask(__name__, static_folder='static')
csrf = CSRFProtect(app)

# Configuración según entorno
if 'WEBSITE_HOSTNAME' not in os.environ:
    print("Loading config.development and environment variables from .env file.")
    app.config.from_object('azureproject.development')
else:
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

# Configuración de la base de datos
app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Inicializar base de datos y migraciones
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# === MODELO DE DATOS ===
class ImagenProcesada(db.Model):
    __tablename__ = 'imagen_procesada'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    nombre_archivo = db.Column(db.String(100))
    rojo = db.Column(db.Integer)
    verde = db.Column(db.Integer)
    azul = db.Column(db.Integer)
    fecha_hora = db.Column(db.DateTime)

    def __str__(self):
        return f"{self.usuario} - {self.nombre_archivo} ({self.fecha_hora})"

# === RUTAS ===

# Página principal
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Ruta para recibir datos desde la app Scala
@app.route('/registro', methods=['POST'])
@csrf.exempt
def registro():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibió JSON'}), 400

    try:
        imagen = ImagenProcesada(
            usuario=data.get('usuario'),
            nombre_archivo=data.get('nombreArchivo'),
            rojo=int(data.get('rojo')),
            verde=int(data.get('verde')),
            azul=int(data.get('azul')),
            fecha_hora=datetime.fromisoformat(data.get('fechaHora'))
        )
        db.session.add(imagen)
        db.session.commit()
        return jsonify({'mensaje': 'Registro guardado'}), 201
    except Exception as e:
        return jsonify({'error': f'Error procesando datos: {str(e)}'}), 500

# Ruta para obtener datos y mostrarlos en la tabla HTML
@app.route('/datos', methods=['GET'])
def datos():
    registros = ImagenProcesada.query.order_by(ImagenProcesada.fecha_hora.desc()).all()
    return jsonify([
        {
            'usuario': r.usuario,
            'nombreArchivo': r.nombre_archivo,
            'rojo': r.rojo,
            'verde': r.verde,
            'azul': r.azul,
            'fechaHora': r.fecha_hora.isoformat()
        }
        for r in registros
    ])

# Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Ejecutar en local
if __name__ == '__main__':
    app.run()
