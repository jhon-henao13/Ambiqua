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
from datetime import datetime, timedelta
import requests
import json
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask_dance.contrib.google import make_google_blueprint, google
import pathlib
import collection

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)


# Configuración de la clave secreta y la conexión a la base de datos usando variables de entorno
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_predeterminada')  # Asegúrate de que esta clave sea segura en producción

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirige al login si no está autenticado
bcrypt = Bcrypt(app)

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
    systems = db.relationship('System', backref='user', lazy=True)

class Plant(db.Model):
    __tablename__ = 'plants'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    humidity_required = db.Column(db.Integer, nullable=True)  # Cambiado a humidity_required
    last_watered = db.Column(db.DateTime, nullable=True)  # Cambiado a last_watered
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    sensor_data = db.relationship('SensorData', backref='plant', lazy=True)

class System(db.Model):
    __tablename__ = 'systems'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    esp32_id = db.Column(db.String(50), unique=True, nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    connection_type = db.Column(db.String(20), nullable=False)
    security_key = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_connection = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active')

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------- Rutas de Autenticación y demás ----------------------

# Configuracion de SendGrid
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
PASSWORD_OF_APP = os.getenv('PASSWORD_OF_APP')

# Serializador para crear y verificar tokens
serializer = Serializer(app.secret_key, salt='password-reset-salt')

# Configuracion de Google OAuth
# Configurar el blueprint correctamente
google_bp = make_google_blueprint(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    redirect_to='google_login_callback',
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ]   # Google ahora requiere estos valores exactos
)

app.register_blueprint(google_bp, url_prefix="/google_login") # <-- Flask-Dance usa "/google_login/google/authorized"

@app.route('/login_google')
def login_google():
    # Redirige a Google para la autentificacion
    return redirect(url_for('google.login'))

@app.route('/google_login/callback')
def google_login_callback():
    # Si el usuario ya esta autenticado, redirigiendo a la pagina principal
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    
    if not google.authorized:
        return redirect(url_for('google.login'))
    
    resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo')

    if not resp.ok:
        flask("Error al obtener información de Google. Intenta nuevamente.", "error")
        return redirect(url_for('login'))
    
    user_info = resp.json()

    # Imprimir la respuesta para depuracion
    print("Respuesta de Google", user_info)

    # Verificar que Google haya enviado un email
    if 'email' not in user_info:
        flash("Error: Google no proporcionó un email.", "error")
        return redirect(url_for('login'))
    
    # Obtener el ID unico de Google
    google_id = user_info.get("sub")

    # Verificar si el usuario ya esta registrado
    user = collection.find_one({'email': user_info['email']})
    if not user:
        # Registrar nuevo usuario con Google
        collection.insert_one({
            'usuario': user_info.get('name', 'Usuario sin nombre'),
            'email': user_info['email'],
            'google_id': google_id # Guardamos el ID único de Google
        })

    # Iniciar sesion guardando el nombre en la sesion
    session['usuario'] = user_info.get('name', 'Usuario sin nombre')

    return redirect(url_for('dashboard'))


# Función para enviar correos
def enviar_email(destinatario, asunto, cuerpo):
    remitente = 'estiguar.dev.emails@gmail.com'  # Cambia esto por tu correo de Gmail
    contraseña = (PASSWORD_OF_APP)  # Cambia esto por tu contraseña de Gmail o contraseña de aplicación

    # Crear el mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto
    mensaje.attach(MIMEText(cuerpo, 'html'))  # Asegúrate de que el cuerpo sea HTML

    try:
        # Conectar al servidor SMTP de Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()  # Iniciar la conexión segura
            servidor.login(remitente, contraseña)  # Iniciar sesión
            servidor.send_message(mensaje)  # Enviar el mensaje
            print(f"Correo enviado a {destinatario} con éxito.")
    except Exception as e:
        print(f'Error al enviar el correo: {e}')
# Redirigir la raiz a login o dashboard según autenticación
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# Formulario de Login
class LoginForm(FlaskForm):
    # email = StringField('Email', validators=[DataRequired(), Email()])
    identifier = StringField('Correo electrónico o usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')

# Ruta para el login (mostrar formulario y procesar inicio de sesión)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data
        password = form.password.data
        
        # Intentar encontrar al usuario por email o nombre de usuario
        user = User.query.filter((User .email == identifier) | (User .username == identifier)).first()

        if user and bcrypt.check_password_hash(user.password, password):  # Cambia esto
            login_user(user, remember=form.remember.data)
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas. Intenta nuevamente.', '❌')
    
    return render_template('login.html', form=form)


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

        # Hashear la contraseña usando flask_bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        flash('Registro exitoso. Inicia sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


# Ruta protegida: Dashboard (panel principal)
@app.route('/dashboard')
@login_required
def dashboard():
    systems = System.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, systems=systems)

# Ruta para la gestion de cultivos
@app.route('/cultivos')
@login_required
def cultivos():
    plants = Plant.query.filter_by(user_id=current_user.id).all()
    return render_template('cultivos.html', user=current_user, plants=plants)



# Ruta para ingresar el correo para recuperar contraseña
@app.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        usuario = User.query.filter_by(email=email).first()

        if usuario:
            # Crear un token para el restablecimiento de contraseña
            token = serializer.dumps(email, salt='password-reset-salt')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            asunto = 'RECUPERACIÓN DE CONTRASEÑA EN AMBIQUA 🌱'

            # Cargar logo en el mensaje del cuerpo del email de recuperacion de contraseña
            logo_url = url_for('static', filename='images/logo.jpg', _external=True)

            cuerpo = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        background-color: #f4f4f4;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: auto;
                        background-color: #ffffff;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                        text-align: center; /* Centrar el contenido */
                    }}

                    #title {{
                        color: #4CAF50; /* Color verde similar a Duolingo */
                        font-weight: 900;
                        font-size: 35px;
                        margin-bottom: 10px;
                        background: none; /* Sin fondo */
                    }}
                    p {{
                        color: #555;
                        font-size: 16px;
                        line-height: 1.5;
                        margin: 10px 0; /* Espaciado entre párrafos */
                    }}

                    a {{
                        display: inline-block;
                        margin-top: 20px;
                        padding-bottom: 17px;
                        background-color: none; /* Color verde */
                        text-decoration: none;
                        border-radius: 7px;
                        font-size: 35px;
                        transition: background-color 0.3s, transform 0.3s;
                        color: #58cc02 !important;
                        font-weight: 900 !important;
                    }}

                    .cambiar-pass {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 12px 20px;
                        background-color: #4CAF50; /* Color verde */
                        text-decoration: none;
                        border-radius: 7px;
                        font-size: 18px;
                        transition: background-color 0.3s, transform 0.3s;
                        color: white !important;
                        font-weight: 900 !important;
                    }}

                    .cambiar-pass:hover {{
                        background-color: #45a049; /* Color verde más oscuro */
                        transform: translateY(-2px);
                    }}
                    .footer {{
                        margin-top: 30px;
                        font-size: 12px;
                        color: #aaa;
                    }}
                    img {{
                        width: 120px;
                        height: auto;
                        border-radius: 20px;
                        margin-bottom: 20px;
                    }}

                    strong {{
                        font-weight: 900;
                    }}

                    @media (max-width: 600px) {{
                        .container {{
                            padding: 15px;
                        }}
                        .title {{
                            font-size: 20px;
                        }}
                        a {{
                            font-size: 16px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <img src="{logo_url}" alt="Ambiqua Logo">
                    <h2 id="title">Hola {usuario.username}!</h2>
                    <p>Hemos recibido una solicitud para cambiar tu contraseña.</p>
                    <p>Si no has solicitado nada, puedes ignorar este mensaje.</p>
                    <p>Para cambiar tu contraseña, haz clic en el siguiente enlace:</p>
                    <a class="cambiar-pass" href="{enlace}">Cambiar contraseña</a>
                    <div class="footer">
                        <p>Gracias por usar <strong>Ambiqua.</strong></p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Enviar el correo
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
        
        if not nueva_contrasena:
            flash('La nueva contraseña no puede estar vacía.', 'error')
            return redirect(url_for('restablecer_contrasena', token=token))

        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        
        usuario = User.query.filter_by(email=email).first()
        if usuario:
            usuario.password = hashed_password
            db.session.commit()  # Guarda el nuevo hash de la contraseña en la base de datos
            flash('Cambiastes tu contraseña con éxito.', 'success')
            return redirect(url_for('login'))
        else:
            flash('No se encontró el usuario.', 'error')

    return render_template('restablecer_contrasena.html', token=token)

# Ruta de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('login'))

# ---------------------- Endpoints API ----------------------

@app.route('/api/systems', methods=['POST'])
@login_required
def add_system():
    data = request.get_json()
    new_system = System(
        user_id=current_user.id,
        name=data['name'],
        esp32_id=data['esp32Id'],
        ip_address=data['ipAddress'],
        connection_type=data['connectionType'],
        security_key=generate_password_hash(data['securityKey'])
    )
    db.session.add(new_system)
    db.session.commit()
    return jsonify({"success": True, "system": {"id": new_system.id, "name": new_system.name}})

@app.route('/api/plants', methods=['POST'])
@login_required
def add_plant():
    data = request.get_json()
    new_plant = Plant(
        user_id=current_user.id,
        name=data['name'],
        humidity_required=data['humidityRequired']
    )
    db.session.add(new_plant)
    db.session.commit()
    return jsonify({"success": True, "plant": {"id": new_plant.id, "name": new_plant.name}})

@app.route('/api/sensor-data', methods=['POST'])
@login_required
def add_sensor_data():
    data = request.get_json()
    new_data = SensorData(
        plant_id=data['plantId'],
        humidity=data['humidity'],
        temperature=data['temperature']
    )
    db.session.add(new_data)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/valve', methods=['POST'])
@login_required
def control_valve():
    data = request.get_json()
    system_id = data.get('systemId')
    action = data.get('action')
    
    system = System.query.get(system_id)
    if not system or system.user_id != current_user.id:
        return jsonify({"success": False, "error": "Sistema no encontrado"})
    
    try:
        response = requests.post(
            f"http://{system.ip_address}/valve",
            json={"action": action, "key": system.security_key},
            timeout=5
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/plants/<int:plant_id>', methods=['DELETE'])
@login_required
def delete_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    if plant.user_id != current_user.id:
        return jsonify({"success": False, "error": "No autorizado"})
    
    db.session.delete(plant)
    db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
