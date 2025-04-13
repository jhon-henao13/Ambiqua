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