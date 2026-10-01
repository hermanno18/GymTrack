/*
 * GymTrack app-shell service worker.
 *
 * Deliberately conservative: this app is a multi-user, authenticated
 * Flask app, not a static site, so the caching strategy is split by
 * request type to avoid ever serving stale/wrong-user dynamic content:
 *
 *   - Non-GET requests (workout saves, logins, CSRF-protected POSTs):
 *     never intercepted -- always go straight to the network.
 *   - Cross-origin requests (Tailwind/htmx/Chart.js CDNs): never
 *     intercepted either -- browser HTTP cache handles those fine, and
 *     intercepting opaque cross-origin responses is a known foot-gun.
 *   - HTML navigations: network-first, falling back to a cached page
 *     only when truly offline (so logged-in users always see fresh
 *     data when they have a connection).
 *   - Same-origin /static/ assets: cache-first with a background
 *     refresh (stale-while-revalidate) -- these rarely change and are
 *     safe to serve instantly from cache.
 */
const CACHE_NAME = 'gymtrack-shell-v1';
const APP_SHELL = [
  '/static/manifest.json',
  '/static/app.css',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL).catch(() => {}))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(() => caches.match(req).then((cached) => cached || caches.match('/')))
    );
    return;
  }

  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const networkFetch = fetch(req)
          .then((res) => {
            caches.open(CACHE_NAME).then((cache) => cache.put(req, res.clone()));
            return res;
          })
          .catch(() => cached);
        return cached || networkFetch;
      })
    );
  }
});
