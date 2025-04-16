document.addEventListener('DOMContentLoaded', () => {
    // Inicializar modales
    Modal.init('systemModal');
    Modal.init('configModal');

    // Configurar eventos del dashboard
    setupDashboardEvents();
    setupRealTimeUpdates();
});

function setupDashboardEvents() {
    // Botón para agregar sistema
    document.getElementById('addSystemBtn').addEventListener('click', () => {
        Modal.open('systemModal');
    });

    // Formulario de sistema
    document.getElementById('systemForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await FormHandler.submitForm('systemForm', '/api/systems', (result) => {
            Modal.close('systemModal');
            location.reload();
        });
    });

    // Control de válvula
    document.getElementById('toggleValveBtn').addEventListener('click', async () => {
        const systemId = document.getElementById('currentSystemId').value;
        const action = document.getElementById('valveStatus').textContent === 'Abierta' ? 'close' : 'open';
        
        const result = await ESP32Handler.controlValve(systemId, action);
        if (result && result.success) {
            updateValveStatus(action === 'open');
            FormHandler.showSuccess('Válvula ' + (action === 'open' ? 'abierta' : 'cerrada') + ' correctamente');
        }
    });

    // Configuración del sistema
    document.getElementById('saveConfigBtn').addEventListener('click', async () => {
        const systemId = document.getElementById('currentSystemId').value;
        const threshold = document.getElementById('humidityThreshold').value;

        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    systemId,
                    threshold
                })
            });

            if (response.ok) {
                FormHandler.showSuccess('Configuración guardada');
                Modal.close('configModal');
            }
        } catch (error) {
            FormHandler.showError('Error al guardar la configuración');
        }
    });
}

function setupRealTimeUpdates() {
    // Actualizar datos cada 30 segundos
    setInterval(updateSensorData, 30000);
    updateSensorData(); // Actualizar inmediatamente al cargar
}

async function updateSensorData() {
    const systemId = document.getElementById('currentSystemId').value;
    const data = await ESP32Handler.getSensorData(systemId);

    if (data) {
        updateSensorDisplay(data);
        updateCharts(data);
        checkAlerts(data);
    }
}

function updateSensorDisplay(data) {
    document.getElementById('humidityValue').textContent = `${data.humidity}%`;
    document.getElementById('temperatureValue').textContent = `${data.temperature}°C`;
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
}

function updateValveStatus(isOpen) {
    const statusElement = document.getElementById('valveStatus');
    const buttonElement = document.getElementById('toggleValveBtn');
    
    statusElement.textContent = isOpen ? 'Abierta' : 'Cerrada';
    statusElement.className = isOpen ? 'status-open' : 'status-closed';
    buttonElement.textContent = isOpen ? 'Cerrar Válvula' : 'Abrir Válvula';
}

function updateCharts(data) {
    // Actualizar gráficos si existen
    const humidityChart = window.humidityChart;
    const temperatureChart = window.temperatureChart;

    if (humidityChart) {
        ChartHandler.updateChart(humidityChart, {
            labels: [...humidityChart.data.labels, new Date().toLocaleTimeString()],
            datasets: [{
                ...humidityChart.data.datasets[0],
                data: [...humidityChart.data.datasets[0].data, data.humidity]
            }]
        });
    }

    if (temperatureChart) {
        ChartHandler.updateChart(temperatureChart, {
            labels: [...temperatureChart.data.labels, new Date().toLocaleTimeString()],
            datasets: [{
                ...temperatureChart.data.datasets[0],
                data: [...temperatureChart.data.datasets[0].data, data.temperature]
            }]
        });
    }
}

function checkAlerts(data) {
    const threshold = parseInt(document.getElementById('humidityThreshold').value);
    
    if (data.humidity < threshold) {
        NotificationHandler.showNotification('Alerta de Humedad', {
            body: `La humedad (${data.humidity}%) está por debajo del umbral (${threshold}%)`,
            icon: '/static/images/alert.png'
        });
    }
}

// Inicializar gráficos
function initCharts() {
    const ctx1 = document.getElementById('humidityChart').getContext('2d');
    const ctx2 = document.getElementById('temperatureChart').getContext('2d');

    window.humidityChart = ChartHandler.init('humidityChart', 'line', {
        labels: [],
        datasets: [{
            label: 'Humedad (%)',
            data: [],
            borderColor: '#58CC02',
            tension: 0.1
        }]
    }, {
        scales: {
            y: {
                beginAtZero: true,
                max: 100
            }
        }
    });

    window.temperatureChart = ChartHandler.init('temperatureChart', 'line', {
        labels: [],
        datasets: [{
            label: 'Temperatura (°C)',
            data: [],
            borderColor: '#FFB800',
            tension: 0.1
        }]
    }, {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    });
} 