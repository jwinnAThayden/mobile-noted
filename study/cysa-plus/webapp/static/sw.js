/* Offline cache. Everything the app needs is precached on install, so after
 * the first load it runs with the network off and survives being installed
 * to the home screen.
 *
 * VERSION is rewritten by build_content.py from a hash of the content, so a
 * rebuild invalidates the old cache automatically.
 */
var VERSION = '0c78efb068';
var CACHE = 'cysa-' + VERSION;
var SHELL = [
  './', 'index.html', 'content.json',
  'css/app.css', 'js/app.js', 'js/tts.js', 'js/cards.js',
  'manifest.webmanifest', 'icons/icon.svg', 'icons/icon-192.png', 'icons/icon-512.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(SHELL); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k !== CACHE) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(function (hit) {
      if (hit) return hit;
      return fetch(e.request).then(function (res) {
        // Cache same-origin successes so later visits work offline too.
        if (res && res.ok && new URL(e.request.url).origin === location.origin) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(e.request, copy); });
        }
        return res;
      }).catch(function () {
        // Offline and not cached: fall back to the shell for navigations.
        if (e.request.mode === 'navigate') return caches.match('index.html');
        throw new Error('offline');
      });
    })
  );
});
