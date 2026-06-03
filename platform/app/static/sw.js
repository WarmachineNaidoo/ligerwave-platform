var CACHE_NAME = 'ligerwave-v2';
var STATIC_ASSETS = [
  '/', '/manifest.json', '/favicon.svg', '/dashboard.html',
  'https://cdn.jsdelivr.net/npm/chart.js@4',
  'https://unpkg.com/@supabase/supabase-js@2'
];

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(STATIC_ASSETS);
    }).then(self.skipWaiting())
  );
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.filter(function(k) { return k !== CACHE_NAME; }).map(function(k) { return caches.delete(k); }));
    }).then(self.clients.claim())
  );
});

self.addEventListener('fetch', function(e) {
  if (e.request.method !== 'GET') return;
  var url = e.request.url;
  // API calls: network first, cache fallback
  if (url.includes('/auth/') || url.includes('/rest/v1/') || url.includes('/events/') || url.includes('/ar/') || url.includes('/wellness/') || url.includes('/push/') || url.includes('/settings/') || url.includes('/export/') || url.includes('/premium/') || url.includes('/homes') || url.includes('/devices/') || url.includes('/zones/')) {
    e.respondWith(
      fetch(e.request).then(function(response) {
        return caches.open(CACHE_NAME).then(function(cache) {
          cache.put(e.request, response.clone());
          return response;
        });
      }).catch(function() {
        return caches.match(e.request).then(function(cached) {
          return cached || caches.match('/');
        });
      })
    );
    return;
  }
  // Static assets: cache first
  if (url.match(/\.(html|js|css|json|svg|png|jpg|ico|webp)$/) || url.match(/\/i18n\//)) {
    e.respondWith(
      caches.match(e.request).then(function(cached) {
        var fetchPromise = fetch(e.request).then(function(response) {
          caches.open(CACHE_NAME).then(function(cache) { cache.put(e.request, response.clone()); });
          return response;
        });
        return cached || fetchPromise;
      })
    );
    return;
  }
  e.respondWith(fetch(e.request));
});

self.addEventListener('push', function(e) {
  var data = {};
  try { data = e.data.json(); } catch(ex) { data = {title: 'Ligerwave Alert', body: e.data.text()}; }
  var title = data.title || 'Ligerwave Security';
  var options = {
    body: data.body || 'Security event detected',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    tag: 'ligerwave-' + Date.now(),
    vibrate: [200, 100, 200],
    requireInteraction: true
  };
  e.waitUntil(
    self.registration.showNotification(title, options).then(function() {
      // Notify all dashboard clients
      return self.clients.matchAll({type: 'window'}).then(function(clients) {
        clients.forEach(function(c) {
          c.postMessage({type: 'push', title: title, body: options.body});
        });
      });
    })
  );
});

self.addEventListener('notificationclick', function(e) {
  e.notification.close();
  e.waitUntil(
    clients.matchAll({type: 'window', includeUncontrolled: true}).then(function(clientList) {
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if (client.url.indexOf('/dashboard.html') >= 0 || client.url === self.registration.scope) {
          return client.focus();
        }
      }
      return clients.openWindow('/dashboard.html');
    })
  );
});
