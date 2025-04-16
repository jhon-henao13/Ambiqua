document.addEventListener('DOMContentLoaded', () => {
    // Inicializar modales
    Modal.init('addPlantModal');
    Modal.init('editPlantModal');

    // Configurar eventos de cultivos
    setupPlantsEvents();
    loadPlants();
});

function setupPlantsEvents() {
    // Botón para agregar cultivo
    document.getElementById('addPlantBtn').addEventListener('click', () => {
        Modal.open('addPlantModal');
    });

    // Formulario de nuevo cultivo
    document.getElementById('plantForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await FormHandler.submitForm('plantForm', '/api/plants', (result) => {
            Modal.close('addPlantModal');
            loadPlants();
        });
    });

    // Delegación de eventos para botones de acción
    document.getElementById('plant-list').addEventListener('click', async (e) => {
        const target = e.target.closest('.action-btn');
        if (!target) return;

        const plantCard = target.closest('.plant-card');
        const plantId = plantCard.dataset.plantId;
        const action = target.classList.contains('edit-btn') ? 'edit' : 'delete';

        if (action === 'edit') {
            openEditModal(plantId);
        } else {
            await deletePlant(plantId);
        }
    });
}

async function loadPlants() {
    try {
        const response = await fetch('/api/plants');
        const plants = await response.json();

        const plantsGrid = document.getElementById('plant-list');
        plantsGrid.innerHTML = '';

        if (plants.length === 0) {
            plantsGrid.innerHTML = `
                <div class="empty-state">
                    <img src="/static/images/empty.svg" alt="Sin cultivos" class="empty-image">
                    <p class="empty-text">Aún no tienes cultivos registrados</p>
                    <button class="btn-add" onclick="Modal.open('addPlantModal')">
                        <span class="btn-icon">+</span>
                        <span class="btn-text">Agregar mi primer cultivo</span>
                    </button>
                </div>
            `;
            return;
        }

        plants.forEach(plant => {
            const plantCard = createPlantCard(plant);
            plantsGrid.appendChild(plantCard);
        });
    } catch (error) {
        FormHandler.showError('Error al cargar los cultivos');
    }
}

function createPlantCard(plant) {
    const card = document.createElement('div');
    card.className = 'plant-card animate-fade-in';
    card.dataset.plantId = plant.id;

    card.innerHTML = `
        <div class="plant-header">
            <h3 class="plant-name">${plant.name}</h3>
            <span class="plant-status" data-status="active">
                <span class="status-icon">🌿</span>
                <span class="status-text">Activo</span>
            </span>
        </div>
        
        <div class="plant-metrics">
            <div class="metric-item">
                <div class="metric-icon">💧</div>
                <div class="metric-info">
                    <div class="metric-value">${plant.humidity_required}%</div>
                    <div class="metric-label">Humedad Requerida</div>
                </div>
            </div>
            
            <div class="metric-item">
                <div class="metric-icon">🌡️</div>
                <div class="metric-info">
                    <div class="metric-value">${plant.temperature || '--'}°C</div>
                    <div class="metric-label">Temperatura Actual</div>
                </div>
            </div>
        </div>
        
        <div class="plant-actions">
            <button class="action-btn edit-btn">
                <span class="btn-icon">✏️</span>
                <span class="btn-text">Editar</span>
            </button>
            <button class="action-btn delete-btn">
                <span class="btn-icon">🗑️</span>
                <span class="btn-text">Eliminar</span>
            </button>
        </div>
    `;

    return card;
}

async function deletePlant(plantId) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#FF4B4B',
        cancelButtonColor: '#58CC02',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (result.isConfirmed) {
        try {
            const response = await fetch(`/api/plants/${plantId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                FormHandler.showSuccess('Cultivo eliminado correctamente');
                loadPlants();
            }
        } catch (error) {
            FormHandler.showError('Error al eliminar el cultivo');
        }
    }
}

function openEditModal(plantId) {
    // Implementar lógica para abrir el modal de edición
    // y cargar los datos del cultivo
    Modal.open('editPlantModal');
    // Cargar datos del cultivo y actualizar el formulario
} 