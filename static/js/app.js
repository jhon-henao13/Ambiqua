console.log("Hola mundo");

// Ejemplo de variables globales
let humidity = 0;
let temperature = 0;
let valveState = false; // false = cerrada, true = abierta

document.addEventListener('DOMContentLoaded', () => {
  const humidityValue = document.getElementById('humidityValue');
  const temperatureValue = document.getElementById('temperatureValue');
  const toggleValveBtn = document.getElementById('toggleValveBtn');
  const humidityThresholdInput = document.getElementById('humidityThreshold');
  const saveConfigBtn = document.getElementById('saveConfigBtn');

  // Simular datos al cargar la página
  // En producción, aquí se llamaría a la API o servidor
  humidityValue.textContent = humidity;
  temperatureValue.textContent = temperature;

  // Evento para abrir/cerrar válvula
  toggleValveBtn.addEventListener('click', () => {
    valveState = !valveState;
    // Aquí harías la llamada a la API para cambiar el estado en el ESP32
    alert(`Válvula ahora está: ${valveState ? 'Abierta' : 'Cerrada'}`);
  });

  // Guardar configuración de umbral
  saveConfigBtn.addEventListener('click', () => {
    const threshold = humidityThresholdInput.value;
    // Aquí harías la llamada a la API para guardar el umbral en el ESP32
    alert(`Umbral de humedad guardado: ${threshold}%`);
  });
});


if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('service-worker.js')
  .then(() => console.log('Service Worker registrado'))
  .catch(err => console.log('Error al registrar SW:', error));
  }

  // Espera a que la ventana se cargue completamente
  window.onload = function() {
  // Oculta el splash screen
  var splash = document.getElementById('splash');
  splash.style.display = 'none';
  };


// ICONO DE MOSTRAR/OCULTAR CONTRASEÑA
document.addEventListener("DOMContentLoaded", function () {
  const togglePassword = document.getElementById("togglePassword");
  const passwordField = document.getElementById('password');

  if (togglePassword && passwordField) {
    togglePassword.addEventListener('click', function () {
      const isPassword = passwordField.type === 'password';
      
      // Cambiar tipo de input
      passwordField.type = isPassword ? 'text' : 'password';
      
      // Cambiar icono visual
      this.classList.toggle('fa-eye-slash', isPassword);
      this.classList.toggle('fa-eye', !isPassword);
      
      // Actualizar accesibilidad
      const label = isPassword ? 'Ocultar contraseña' : 'Mostrar contraseña';
      this.setAttribute('aria-label', label);
    });
  }
});

// Aqui se puede agregar cualquier comportamiento dinamico si es necesario
// Ejemplo: Cambiar las iniciales con el nombre del usuario al iniciar sesion
document.addEventListener("DOMContentLoaded", () => {
  // Cambiar las iniciales del usuario (esto depende de la logica Back-End)
  const userInitials = "DN"; // Suponiendo que 'DN' son las iniciales del usuario
  document.getElementById('user-initials').textContent = userInitials;
});