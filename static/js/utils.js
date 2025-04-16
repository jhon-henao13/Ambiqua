// Utilidades para el manejo de modales
const Modal = {
    init(modalId) {
        this.modal = document.getElementById(modalId);
        this.closeBtn = this.modal.querySelector('.close');
        this.setupEvents();
    },

    setupEvents() {
        this.closeBtn.addEventListener('click', () => this.close());
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) this.close();
        });
    },

    open() {
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        this.modal.classList.add('show');
    },

    close() {
        this.modal.classList.remove('show');
        setTimeout(() => {
            this.modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }, 300);
    }
};

// Utilidades para el manejo de formularios
const FormHandler = {
    async submitForm(formId, endpoint, successCallback) {
        const form = document.getElementById(formId);
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (response.ok) {
                if (successCallback) successCallback(result);
                this.showSuccess('Operación exitosa');
            } else {
                this.showError(result.error || 'Error en la operación');
            }
        } catch (error) {
            this.showError('Error de conexión');
            console.error('Error:', error);
        }
    },

    showSuccess(message) {
        Swal.fire({
            title: '¡Éxito!',
            text: message,
            icon: 'success',
            confirmButtonColor: '#58CC02'
        });
    },

    showError(message) {
        Swal.fire({
            title: 'Error',
            text: message,
            icon: 'error',
            confirmButtonColor: '#FF4B4B'
        });
    }
};

// Utilidades para el manejo de datos del ESP32
const ESP32Handler = {
    async getSensorData(systemId) {
        try {
            const response = await fetch(`/api/sensor-data/${systemId}`);
            return await response.json();
        } catch (error) {
            console.error('Error al obtener datos del sensor:', error);
            return null;
        }
    },

    async controlValve(systemId, action) {
        try {
            const response = await fetch('/api/valve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    systemId,
                    action
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error al controlar la válvula:', error);
            return null;
        }
    }
};

// Utilidades para el manejo de gráficos
const ChartHandler = {
    init(chartId, type, data, options) {
        const ctx = document.getElementById(chartId).getContext('2d');
        return new Chart(ctx, {
            type,
            data,
            options: {
                ...options,
                responsive: true,
                maintainAspectRatio: false
            }
        });
    },

    updateChart(chart, newData) {
        chart.data = newData;
        chart.update();
    }
};

// Utilidades para el manejo de notificaciones
const NotificationHandler = {
    async requestPermission() {
        if (!('Notification' in window)) {
            console.log('Las notificaciones no son soportadas');
            return false;
        }

        if (Notification.permission === 'granted') {
            return true;
        }

        const permission = await Notification.requestPermission();
        return permission === 'granted';
    },

    showNotification(title, options) {
        if (Notification.permission === 'granted') {
            new Notification(title, options);
        }
    }
};

// Exportar utilidades
window.Modal = Modal;
window.FormHandler = FormHandler;
window.ESP32Handler = ESP32Handler;
window.ChartHandler = ChartHandler;
window.NotificationHandler = NotificationHandler; 