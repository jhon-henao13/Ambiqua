from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configuración de la clave secreta y la conexión a la base de datos usando variables de entorno
app.secret_key = os.getenv('SECRET_KEY', 'clave_predeterminada')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirige al login si no está autenticado

# Modelo de Usuario con el nombre de tabla correcto
class User(db.Model, UserMixin):
    __tablename__ = 'users'  # Asegura que SQLAlchemy use la tabla 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relación con Plant
    plants = db.relationship('Plant', backref='user', lazy=True)

class Plant(db.Model):
    __tablename__ = 'plants'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    humidity_required = db.Column(db.Integer, nullable=True)  # Cambiado a humidity_required
    last_watered = db.Column(db.DateTime, nullable=True)  # Cambiado a last_watered

    # No es necesario definir la relación aquí, ya que se maneja en User


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------- Rutas de Autenticación y demás ----------------------

# Redirigir la raiz a login o dashboard según autenticación
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard', user=current_user, esp32_status="Conectado", valve_status="Cerrada", humidity=65, temperature=22))
    return redirect(url_for('login'))

# Ruta para el login (mostrar formulario y procesar inicio de sesión)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Procesar login
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas. Intenta nuevamente.', '❌')
            return redirect(url_for('login'))
    return render_template('login.html')

# Ruta para el registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', '❌')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('El nombre de usuario o email ya existe.', '❌')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Registro exitoso. Inicia sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Ruta protegida: Dashboard (panel principal)
@app.route('/dashboard')
@login_required
def dashboard():
    # Aquí se pueden enviar datos relevantes al usuario (ej. lista de cultivos, estado del sistema, etc.)
    return render_template('dashboard.html', user=current_user)

# Ruta para la gestion de cultivos
@app.route('/cultivos')
@login_required
def cultivos():
    return render_template('cultivos.html', user=current_user)


# Ruta de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('login'))

# ---------------------- Endpoints API ----------------------

@app.route('/api/plants', methods=['POST'])
@login_required
def add_plant():
    data = request.get_json()
    new_plant = Plant(user_id=current_user.id, name=data['name'], humidity_required=data['humidity_required'])
    db.session.add(new_plant)
    db.session.commit()
    return jsonify({"success": True, "plant": {"id": new_plant.id, "name": new_plant.name}})

    # GET: Obtener todos los cultivos del usuario
    plants = Plant.query.filter_by(user_id=current_user.id).all()
    return jsonify([{"id": plant.id, "name": plant.name, "humidity": plant.humidity, "temperature": plant.temperature} for plant in plants])


# API para actualizar la configuración (por ejemplo, umbral de humedad)
@app.route('/api/config', methods=['POST'])
@login_required
def update_config():
    data = request.get_json()
    threshold = data.get("threshold")
    # Aquí podrías guardar la configuración en la BD o enviarla al ESP32
    return jsonify({"success": True, "humidityThreshold": threshold})

# API para cambiar el estado de la válvula
@app.route('/api/valve', methods=['POST'])
@login_required
def change_valve_state():
    data = request.get_json()
    valve_open = data.get("open")
    # Aquí se enviaría la orden al ESP32 para abrir o cerrar la válvula
    enviar_comando_valvula(valve_open)
    return jsonify({"success": True, "valveOpen": valve_open})

def enviar_comando_valvula(abrir):
    # Función simulada para enviar el comando al ESP32
    if abrir:
        print("Comando: ABRIR válvula")
    else:
        print("Comando: CERRAR válvula")
    # Aquí se implementa la lógica real de comunicación (HTTP, MQTT, etc.)

if __name__ == '__main__':
    app.run(debug=True)
