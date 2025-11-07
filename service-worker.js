// Service Worker for AI Ambassador Platform PWA
// Version: 1.0.0

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `ai-ambassador-${CACHE_VERSION}`;
const RUNTIME_CACHE = `runtime-${CACHE_VERSION}`;
const IMAGE_CACHE = `images-${CACHE_VERSION}`;
const API_CACHE = `api-${CACHE_VERSION}`;

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/mobile-chat.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/offline.html',
  '/styles/mobile.css',
  '/scripts/mobile-app.js',
  '/scripts/offline-queue.js'
];

// API endpoints
const API_ENDPOINTS = [
  '/api/businessinsightbot_function',
  '/api/ambassador_entry'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
      .catch((error) => {
        console.error('[Service Worker] Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              // Delete old versions
              return cacheName.startsWith('ai-ambassador-') &&
                     cacheName !== CACHE_NAME &&
                     cacheName !== RUNTIME_CACHE &&
                     cacheName !== IMAGE_CACHE &&
                     cacheName !== API_CACHE;
            })
            .map((cacheName) => {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin && !url.pathname.includes('/api/')) {
    return;
  }

  // Handle different types of requests with appropriate strategies
  if (request.method === 'GET') {
    if (isImageRequest(request)) {
      event.respondWith(cacheFirstImage(request));
    } else if (isAPIRequest(request)) {
      event.respondWith(networkFirstAPI(request));
    } else if (isStaticAsset(request)) {
      event.respondWith(cacheFirst(request));
    } else {
      event.respondWith(networkFirst(request));
    }
  } else if (request.method === 'POST') {
    // POST requests - network only with offline queue
    event.respondWith(networkOnlyWithQueue(request));
  }
});

// Cache-first strategy (for static assets)
async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  if (cached) {
    console.log('[Service Worker] Cache hit:', request.url);
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.error('[Service Worker] Fetch failed:', error);
    return caches.match('/offline.html');
  }
}

// Cache-first for images
async function cacheFirstImage(request) {
  const cache = await caches.open(IMAGE_CACHE);
  const cached = await cache.match(request);

  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Return placeholder image
    return new Response(
      '<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg"><rect fill="#f3f4f6" width="400" height="300"/><text x="50%" y="50%" text-anchor="middle" fill="#9ca3af" font-family="sans-serif" font-size="18">Image Unavailable</text></svg>',
      { headers: { 'Content-Type': 'image/svg+xml' } }
    );
  }
}

// Network-first strategy (for API calls)
async function networkFirstAPI(request) {
  const cache = await caches.open(API_CACHE);

  try {
    const response = await fetch(request, { timeout: 5000 });

    if (response.ok) {
      // Only cache GET requests
      if (request.method === 'GET') {
        cache.put(request, response.clone());
      }
    }

    return response;
  } catch (error) {
    console.log('[Service Worker] Network failed, trying cache:', request.url);
    const cached = await cache.match(request);

    if (cached) {
      // Add header to indicate this is from cache
      const headers = new Headers(cached.headers);
      headers.append('X-From-Cache', 'true');

      return new Response(cached.body, {
        status: cached.status,
        statusText: cached.statusText,
        headers: headers
      });
    }

    // Return offline response
    return new Response(JSON.stringify({
      error: 'offline',
      message: 'You are currently offline. This message will be sent when you reconnect.'
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Network-first strategy (for HTML pages)
async function networkFirst(request) {
  const cache = await caches.open(RUNTIME_CACHE);

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
    return caches.match('/offline.html');
  }
}

// Network-only with offline queue
async function networkOnlyWithQueue(request) {
  try {
    return await fetch(request);
  } catch (error) {
    // Queue the request for later
    const body = await request.clone().text();

    await queueRequest({
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      body: body,
      timestamp: Date.now()
    });

    // Trigger background sync if available
    if ('sync' in self.registration) {
      await self.registration.sync.register('sync-messages');
    }

    return new Response(JSON.stringify({
      queued: true,
      message: 'Your message has been queued and will be sent when you reconnect.'
    }), {
      status: 202,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Helper functions
function isImageRequest(request) {
  return request.destination === 'image' ||
         /\.(jpg|jpeg|png|gif|svg|webp|ico)$/i.test(new URL(request.url).pathname);
}

function isAPIRequest(request) {
  return request.url.includes('/api/');
}

function isStaticAsset(request) {
  const url = new URL(request.url);
  return STATIC_ASSETS.some(asset => url.pathname === asset) ||
         /\.(css|js|json)$/i.test(url.pathname);
}

// Queue management
async function queueRequest(requestData) {
  const db = await openDatabase();
  const tx = db.transaction('queue', 'readwrite');
  const store = tx.objectStore('queue');

  await store.add(requestData);
}

async function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('AIAmbassadorDB', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains('queue')) {
        const store = db.createObjectStore('queue', {
          keyPath: 'id',
          autoIncrement: true
        });
        store.createIndex('timestamp', 'timestamp', { unique: false });
      }

      if (!db.objectStoreNames.contains('conversations')) {
        const store = db.createObjectStore('conversations', {
          keyPath: 'id',
          autoIncrement: true
        });
        store.createIndex('ambassadorId', 'ambassadorId', { unique: false });
        store.createIndex('timestamp', 'timestamp', { unique: false });
      }
    };
  });
}

// Background sync event
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncQueuedMessages());
  }
});

async function syncQueuedMessages() {
  const db = await openDatabase();
  const tx = db.transaction('queue', 'readonly');
  const store = tx.objectStore('queue');
  const requests = await store.getAll();

  console.log('[Service Worker] Syncing queued messages:', requests.length);

  for (const requestData of requests) {
    try {
      const response = await fetch(requestData.url, {
        method: requestData.method,
        headers: requestData.headers,
        body: requestData.body
      });

      if (response.ok) {
        // Remove from queue
        const deleteTx = db.transaction('queue', 'readwrite');
        const deleteStore = deleteTx.objectStore('queue');
        await deleteStore.delete(requestData.id);

        // Notify client
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
          client.postMessage({
            type: 'MESSAGE_SYNCED',
            requestId: requestData.id
          });
        });
      }
    } catch (error) {
      console.error('[Service Worker] Sync failed for request:', requestData.id, error);
    }
  }
}

// Push notification event
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push notification received');

  let data = {
    title: 'AI Ambassador',
    body: 'You have a new message',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    tag: 'ambassador-message',
    requireInteraction: false
  };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (error) {
      data.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon,
      badge: data.badge,
      tag: data.tag,
      requireInteraction: data.requireInteraction,
      vibrate: [200, 100, 200],
      data: data.data || {},
      actions: [
        {
          action: 'open',
          title: 'Open',
          icon: '/icons/open-icon.png'
        },
        {
          action: 'dismiss',
          title: 'Dismiss',
          icon: '/icons/close-icon.png'
        }
      ]
    })
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked:', event.action);

  event.notification.close();

  if (event.action === 'open') {
    const urlToOpen = event.notification.data.url || '/';

    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((windowClients) => {
          // Check if there's already a window open
          for (let client of windowClients) {
            if (client.url === urlToOpen && 'focus' in client) {
              return client.focus();
            }
          }
          // Open new window
          if (clients.openWindow) {
            return clients.openWindow(urlToOpen);
          }
        })
    );
  }
});

// Message event - handle messages from clients
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);

  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys()
        .then((cacheNames) => {
          return Promise.all(
            cacheNames.map((cacheName) => caches.delete(cacheName))
          );
        })
        .then(() => {
          event.ports[0].postMessage({ cleared: true });
        })
    );
  }

  if (event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_VERSION });
  }
});

// Periodic background sync (if supported)
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'sync-ambassadors') {
    event.waitUntil(syncAmbassadors());
  }
});

async function syncAmbassadors() {
  console.log('[Service Worker] Syncing ambassadors in background');
  // Fetch latest ambassador data
  try {
    const response = await fetch('/api/ambassadors/sync');
    if (response.ok) {
      const cache = await caches.open(API_CACHE);
      cache.put('/api/ambassadors/sync', response.clone());
    }
  } catch (error) {
    console.error('[Service Worker] Background sync failed:', error);
  }
}

console.log('[Service Worker] Loaded version:', CACHE_VERSION);
