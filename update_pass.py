from app import app, db, User, bcrypt

# Crear un contexto de aplicación
with app.app_context():
    # Establecer nueva contraseña para el usuario admin
    usuario_admin = User.query.filter_by(username='prueba').first()
    if usuario_admin:
        nueva_contrasena = '12345'  # Cambia esto por una contraseña segura
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        usuario_admin.password = hashed_password
        db.session.commit()
        print("Contraseña actualizada para el usuario prueba.")
    else:
        print("Usuario admin no encontrado.")