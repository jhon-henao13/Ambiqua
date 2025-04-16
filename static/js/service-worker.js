const CACHE_NAME = 'ambiqua-cache-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/base.css',
    '/static/css/dashboard.css',
    '/static/css/plants.css',
    '/static/css/animations.css',
    '/static/js/utils.js',
    '/static/js/dashboard.js',
    '/static/js/plants.js',
    '/static/images/letraA.png',
    '/static/images/empty.svg',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png'
];

// Instalación del Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Cache abierto');
                return cache.addAll(ASSETS_TO_CACHE);
            })
    );
});

// Activación del Service Worker
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Eliminando cache antiguo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Estrategia de caché: Network First, Cache Fallback
self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Clonar la respuesta
                const responseClone = response.clone();
                
                // Abrir el caché
                caches.open(CACHE_NAME)
                    .then((cache) => {
                        // Guardar la respuesta en el caché
                        cache.put(event.request, responseClone);
                    });
                
                return response;
            })
            .catch(() => {
                // Si falla la red, intentar servir desde el caché
                return caches.match(event.request)
                    .then((response) => {
                        if (response) {
                            return response;
                        }
                        
                        // Si no está en el caché, mostrar una página offline
                        if (event.request.mode === 'navigate') {
                            return caches.match('/offline.html');
                        }
                    });
            })
    );
});

// Manejo de notificaciones push
self.addEventListener('push', (event) => {
    const data = event.data.json();
    
    const options = {
        body: data.body,
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/badge.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Manejo de clics en notificaciones
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
  