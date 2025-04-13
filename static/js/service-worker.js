self.addEventListener('install', event => {
    console.log('Service Worker: Instalado');
  });
  
  self.addEventListener('fetch', event => {
    // Podrías cachear archivos aquí si lo deseas
  });
  