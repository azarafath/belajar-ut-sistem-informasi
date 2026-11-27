const CACHE_NAME = 'belajar-ut-v21';
const CORE_ASSETS = [
  '/',
  '/index.html',
  '/styles.css',
  '/search-index.json',
  '/manifest.webmanifest',
  '/icon.svg',
  '/icon-192.png',
  '/icon-512.png',
  '/smt1/perilaku-organisasi.html',
  '/smt1/sim-manajemen.html',
  '/smt1/aljabar-linear-elementer.html',
  '/smt1/belajar-di-era-digital.html',
  '/smt1/struktur-data.html',
  '/smt1/interaksi-manusia-komputer.html',
  '/smt1/rekayasa-perangkat-lunak.html',
  '/smt2/basis-data.html',
  '/smt2/proses-bisnis.html',
  '/smt2/analisis-visualisasi-data.html',
  '/smt2/komunikasi-bisnis-teknis.html',
  '/smt2/sistem-informasi-manajemen.html',
  '/smt2/tata-kelola-ti.html',
  '/smt2/analisis-perancangan-sistem.html',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Cache-first for Google Fonts so typography renders instantly with zero FOUT
  if (url.origin === 'https://fonts.googleapis.com' || url.origin === 'https://fonts.gstatic.com') {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) =>
        cache.match(req).then(
          (cached) =>
            cached ||
            fetch(req).then((res) => {
              if (res && res.status === 200) cache.put(req, res.clone());
              return res;
            })
        )
      )
    );
    return;
  }

  if (url.origin !== self.location.origin) return;

  // Network-first so deployed updates show up right away, with offline cache fallback
  event.respondWith(
    fetch(req)
      .then((res) => {
        if (res && res.status === 200) {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        }
        return res;
      })
      .catch(() => caches.match(req).then((cached) => cached || caches.match('/index.html')))
  );
});

