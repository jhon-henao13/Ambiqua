from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_bcrypt import Bcrypt


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

# Configuracion de SendGrid
SENDGRID_API_KEY = '(api)'

# Serializador para crear y verificar tokens
serializer = Serializer(app.secret_key, salt='password-reset-salt')

# Funcion para enviar correos
def enviar_email(destinatario, asunto, cuerpo):
    mensaje = Mail(
        from_email='estiguar.dev.emails@gmail.com', # Cambiar por el correo nuevo exclusivo para enviar emails de recuperacion
        to_emails=destinatario,
        subject=asunto,
        html_content=cuerpo
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY) # Usar clave API de SendGrid directamente
        response = sg.send(mensaje)
        print(f"Correo enviado con éxito! Status code: {response.status.code}")
    except Exception as e:
        print(f'Error al enviar el correo: {e}')



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


# Ruta para ingresar el correo para recuperar contraseña
@app.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        usuario = collection.find_one({'email': email})

        if usuario:
            token = serializer.dumps(email, salt='password-reset-salt')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            asunto = 'RECUPERACIÓN DE CONTRASEÑA EN AMBIQUA 🌱'
            cuerpo = f"""
            <p>Hola!, hemos recibido una solicitud para cambiar tu contraseña.</p>
            <p>Si no has solicitado nada, entonces puedes ignorar este mensaje.</p>
            <p>Para cambiar tu contraseña, haz clic en el siguiente link:</p>
            <a href="{enlace}">Cambiar contraseña</a>
            """

            enviar_email(email, asunto, cuerpo)
            flash('Correo enviado para que cambies tu contraseña.', 'success')
        else:
            flash('El correo no existe en nuestro sistema.', 'error')

    return render_template('recuperar_contrasena.html')


# Ruta para cambiar o restablecer la contraseña
@app.route('/restablecer_contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('El link para cambiar tu contraseña ha vencido o es erróneo.', 'error')
        return redirect(url_for('recuperar_contrasena'))

    if request.method == 'POST':
        nueva_contrasena = request.form['nueva_contrasena']
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        collection.update_one({'email': email}, {'$set': {'contrasena': hashed_password}})
        flash('Cambiastes tu contraseña con éxito.', 'success')
        return redirect(url_for('login'))

    return render_template('restablecer_contrasena.html')



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
