# AI Ambassador Platform - Progressive Web App Guide

## Overview

This guide covers the Progressive Web App (PWA) implementation for the AI Ambassador Platform, providing a native app-like experience for discovering and interacting with AI Ambassadors on mobile devices.

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Service Worker](#service-worker)
5. [Offline Support](#offline-support)
6. [Push Notifications](#push-notifications)
7. [Performance](#performance)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## Features

### Core PWA Features

- **Installable**: Add to home screen on iOS and Android
- **Offline-First**: Works without internet connection
- **Fast**: < 3 second load time on 3G
- **Responsive**: Optimized for all screen sizes
- **App-Like**: Standalone display mode
- **Push Notifications**: Re-engagement via notifications
- **Background Sync**: Queue messages when offline
- **Pull-to-Refresh**: Update conversations
- **Touch-Optimized**: 44x44px minimum touch targets
- **Haptic Feedback**: Vibration on interactions

### Mobile-Specific Features

- **Voice Input**: Web Speech API integration
- **Image Sharing**: Camera and gallery access
- **Location Sharing**: Geolocation API
- **Swipe Gestures**: Natural mobile interactions
- **Bottom Navigation**: Thumb-friendly layout
- **Quick Actions**: Frequent action shortcuts
- **Split Screen Support**: Multi-window on Android

---

## Architecture

### File Structure

```
AIGames/
├── manifest.json                    # PWA manifest
├── service-worker.js                # Service worker
├── mobile-chat.html                 # Mobile chat UI
├── offline.html                     # Offline fallback page
├── scripts/
│   ├── mobile-app.js               # Main app logic
│   ├── offline-queue.js            # Offline message queue
│   └── push-notifications.js       # Push notification manager
├── icons/                          # App icons (multiple sizes)
└── Copilot-Agent-365-main/
    └── push_notification_function.py  # Azure Function for push
```

### Technology Stack

- **Frontend**: Vanilla JavaScript (ES6+)
- **Storage**: IndexedDB for offline data
- **Caching**: Cache API + Service Worker
- **Notifications**: Push API + Notification API
- **Backend**: Azure Functions (Python 3.11)
- **Push Service**: Web Push Protocol (VAPID)

---

## Installation

### Prerequisites

1. **HTTPS Required**: PWAs require secure context
   - Production: Use Azure-provided HTTPS
   - Development: Use localhost (automatically secure) or ngrok

2. **Modern Browser**:
   - Chrome/Edge 80+
   - Safari 14.5+
   - Firefox 90+
   - Samsung Internet 14+

### Setup Steps

#### 1. Generate VAPID Keys (for Push Notifications)

```bash
# Install web-push CLI
npm install -g web-push

# Generate VAPID keys
web-push generate-vapid-keys

# Output:
# Public Key: BEl62iUYgUivxIkv69yViEuiBIa-Ib37J8Aa4K7MLW0c...
# Private Key: ...
```

#### 2. Update Configuration

**A. Update `service-worker.js`:**
- Set `CACHE_VERSION` to current version (e.g., 'v1.0.0')

**B. Update `push-notifications.js`:**
```javascript
this.applicationServerKey = 'YOUR_VAPID_PUBLIC_KEY';
```

**C. Update `push_notification_function.py`:**
```python
VAPID_PRIVATE_KEY = "your-vapid-private-key"
VAPID_PUBLIC_KEY = "your-vapid-public-key"
VAPID_CLAIMS = {
    "sub": "mailto:your-email@domain.com"
}
```

#### 3. Generate App Icons

Create icons in the following sizes:
- 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512

**Using ImageMagick:**
```bash
# Create icons directory
mkdir -p icons

# Convert logo to multiple sizes
for size in 72 96 128 144 152 192 384 512; do
  convert logo.png -resize ${size}x${size} icons/icon-${size}x${size}.png
done

# Create maskable icons (with padding)
for size in 72 96 128 144 152 192 384 512; do
  convert logo.png -resize $((size * 80 / 100))x$((size * 80 / 100)) \
    -background transparent -gravity center \
    -extent ${size}x${size} icons/icon-${size}x${size}.png
done
```

**iOS-Specific:**
```bash
# Apple touch icon (180x180)
convert logo.png -resize 180x180 icons/apple-touch-icon.png

# Safari pinned tab icon (vector)
# Create SVG manually or use:
convert logo.png -resize 512x512 icons/safari-pinned-tab.svg
```

#### 4. Update Manifest

Edit `manifest.json` with your app details:
```json
{
  "name": "AI Ambassador Platform",
  "short_name": "AI Ambassadors",
  "description": "Your custom description",
  "theme_color": "#6366f1",
  "background_color": "#ffffff",
  "start_url": "/"
}
```

#### 5. Add to HTML

Include in all HTML files (`<head>` section):
```html
<!-- PWA Manifest -->
<link rel="manifest" href="/manifest.json">

<!-- Meta tags -->
<meta name="theme-color" content="#6366f1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="AI Ambassadors">

<!-- Icons -->
<link rel="icon" type="image/png" sizes="32x32" href="/icons/icon-32x32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/icons/apple-touch-icon.png">
```

---

## Service Worker

### Overview

The service worker (`service-worker.js`) handles:
- Static asset caching
- API response caching
- Offline functionality
- Background sync
- Push notifications
- Cache versioning and cleanup

### Caching Strategies

#### 1. Cache-First (Static Assets)
```javascript
// Used for: HTML, CSS, JS, fonts
// Serves from cache, updates in background
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  cache.put(request, response.clone());
  return response;
}
```

#### 2. Network-First (API Calls)
```javascript
// Used for: API endpoints
// Tries network first, falls back to cache
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    cache.put(request, response.clone());
    return response;
  } catch {
    return caches.match(request);
  }
}
```

#### 3. Cache-First (Images)
```javascript
// Used for: Images, avatars
// Serves from cache, lazy loads new images
async function cacheFirstImage(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  cache.put(request, response.clone());
  return response;
}
```

### Cache Management

**Cache Versioning:**
```javascript
const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `ai-ambassador-${CACHE_VERSION}`;
```

**Cache Cleanup on Activation:**
```javascript
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => cacheName.startsWith('ai-ambassador-') &&
                                 cacheName !== CACHE_NAME)
          .map((cacheName) => caches.delete(cacheName))
      );
    })
  );
});
```

### Updating Service Worker

When you update `service-worker.js`:

1. Increment `CACHE_VERSION`
2. Deploy new version
3. User will see update notification
4. Call `skipWaiting()` to activate immediately

```javascript
// In service worker
self.skipWaiting();

// From client
navigator.serviceWorker.addEventListener('controllerchange', () => {
  window.location.reload();
});
```

---

## Offline Support

### IndexedDB Storage

The app uses IndexedDB for offline data storage:

**Stores:**
- `conversations`: Chat message history
- `queue`: Pending messages to sync

**Schema:**
```javascript
// Conversations store
{
  id: autoIncrement,
  ambassadorId: string,
  role: 'user' | 'assistant',
  content: string,
  timestamp: number
}

// Queue store
{
  id: autoIncrement,
  url: string,
  method: string,
  headers: object,
  body: string,
  timestamp: number,
  status: 'pending' | 'failed',
  retryCount: number
}
```

### Offline Message Queue

Messages sent while offline are queued and synced when connection is restored:

```javascript
// Queue message
await offlineQueue.queueMessage(message, userId, conversationHistory);

// Sync queued messages
await offlineQueue.sync();
```

**Background Sync:**
```javascript
// Register background sync
navigator.serviceWorker.ready.then((registration) => {
  registration.sync.register('sync-messages');
});

// In service worker
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncQueuedMessages());
  }
});
```

### Offline Indicators

**UI Updates:**
- Offline banner shown at top
- Status indicator changes to red
- "Queued" badge on pending messages
- Toast notification when message queued

**Connection Detection:**
```javascript
window.addEventListener('online', () => {
  // Sync messages
  offlineQueue.sync();
});

window.addEventListener('offline', () => {
  // Update UI
  showOfflineBanner();
});
```

---

## Push Notifications

### Client-Side Setup

#### 1. Request Permission

```javascript
const permission = await Notification.requestPermission();

if (permission === 'granted') {
  await subscribeUser();
}
```

#### 2. Subscribe to Push

```javascript
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
});

// Send subscription to server
await fetch('/api/push/subscribe', {
  method: 'POST',
  body: JSON.stringify({
    subscription: subscription.toJSON(),
    userId: userId,
    ambassadorId: ambassadorId
  })
});
```

#### 3. Handle Notifications

```javascript
// In service worker
self.addEventListener('push', (event) => {
  const data = event.data.json();

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icons/icon-192x192.png',
      badge: '/icons/badge-72x72.png',
      vibrate: [200, 100, 200],
      data: data.data,
      actions: [
        { action: 'open', title: 'Open' },
        { action: 'dismiss', title: 'Dismiss' }
      ]
    })
  );
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'open') {
    clients.openWindow(event.notification.data.url);
  }
});
```

### Server-Side Setup

#### 1. Install Dependencies

```bash
cd Copilot-Agent-365-main
pip install pywebpush
```

Add to `requirements.txt`:
```
pywebpush==1.14.0
```

#### 2. Add Function Bindings

Add to `function_app.py`:
```python
@app.route(route="push/{route}", auth_level=func.AuthLevel.ANONYMOUS)
def push_notification(req: func.HttpRequest) -> func.HttpResponse:
    """Handle push notification requests"""
    from push_notification_function import main
    return main(req)
```

#### 3. Environment Variables

Add to `local.settings.json`:
```json
{
  "Values": {
    "VAPID_PUBLIC_KEY": "your-public-key",
    "VAPID_PRIVATE_KEY": "your-private-key",
    "VAPID_SUBJECT": "mailto:support@ai-ambassadors.app"
  }
}
```

#### 4. Send Notifications

```python
# Send to single user
POST /api/push/send
{
  "userId": "user_123",
  "notification": {
    "title": "New Message",
    "body": "You have a new message from Creative Ambassador",
    "data": {
      "url": "/mobile-chat.html?ambassador=creative-001"
    }
  }
}

# Send to multiple users
POST /api/push/send
{
  "userIds": ["user_123", "user_456"],
  "notification": {...}
}
```

### Notification Best Practices

1. **Ask Permission at Right Time**: Don't ask immediately on load
2. **Be Specific**: Clear, actionable notification text
3. **Use Actions**: Provide quick action buttons
4. **Respect Quiet Hours**: Check user preferences
5. **Badge Count**: Update app badge (if supported)
6. **Silent vs Alert**: Use appropriate urgency

---

## Performance

### Performance Budget

- **First Contentful Paint (FCP)**: < 1.5s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Time to Interactive (TTI)**: < 3.0s
- **Cumulative Layout Shift (CLS)**: < 0.1
- **First Input Delay (FID)**: < 100ms
- **Total Blocking Time (TBT)**: < 300ms

### Optimization Techniques

#### 1. Code Splitting

```javascript
// Lazy load features
const loadVoiceRecognition = () => import('./voice-recognition.js');
const loadImageProcessor = () => import('./image-processor.js');
```

#### 2. Image Optimization

```html
<!-- Responsive images -->
<img srcset="image-400.jpg 400w,
             image-800.jpg 800w,
             image-1200.jpg 1200w"
     sizes="(max-width: 400px) 400px,
            (max-width: 800px) 800px,
            1200px"
     src="image-800.jpg"
     loading="lazy"
     alt="Description">

<!-- Modern formats -->
<picture>
  <source srcset="image.webp" type="image/webp">
  <source srcset="image.jpg" type="image/jpeg">
  <img src="image.jpg" alt="Description">
</picture>
```

#### 3. Critical CSS

```html
<style>
  /* Inline critical CSS here */
  body { margin: 0; font-family: sans-serif; }
  .app-container { display: flex; flex-direction: column; }
</style>

<!-- Load full CSS asynchronously -->
<link rel="preload" href="/styles/mobile.css" as="style"
      onload="this.onload=null;this.rel='stylesheet'">
```

#### 4. Resource Hints

```html
<!-- Preconnect to API -->
<link rel="preconnect" href="https://api.ai-ambassadors.app">

<!-- Prefetch next page -->
<link rel="prefetch" href="/collection.html">

<!-- Preload critical assets -->
<link rel="preload" href="/icons/icon-192x192.png" as="image">
```

#### 5. Touch Optimization

```css
/* Remove 300ms tap delay */
* {
  touch-action: manipulation;
}

/* Minimum touch target size */
.button {
  min-width: 44px;
  min-height: 44px;
}

/* Remove tap highlight */
* {
  -webkit-tap-highlight-color: transparent;
}
```

### Performance Monitoring

#### Lighthouse Audit

```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run audit
lighthouse https://your-app-url \
  --only-categories=performance,pwa,accessibility \
  --chrome-flags="--headless" \
  --output=html \
  --output-path=./lighthouse-report.html
```

**Target Scores:**
- Performance: 90+
- PWA: 100
- Accessibility: 90+
- Best Practices: 90+

#### Real User Monitoring

```javascript
// Performance API
const perfData = performance.getEntriesByType('navigation')[0];

console.log('DNS:', perfData.domainLookupEnd - perfData.domainLookupStart);
console.log('TCP:', perfData.connectEnd - perfData.connectStart);
console.log('Request:', perfData.responseStart - perfData.requestStart);
console.log('Response:', perfData.responseEnd - perfData.responseStart);
console.log('DOM:', perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart);
console.log('Load:', perfData.loadEventEnd - perfData.loadEventStart);

// Send to analytics
analytics.send('performance', {
  fcp: perfData.firstContentfulPaint,
  lcp: perfData.largestContentfulPaint,
  tti: perfData.timeToInteractive
});
```

---

## Testing

### Manual Testing

#### Android (Chrome)

1. Open DevTools (F12)
2. Click "Application" tab
3. Check "Service Workers" - should show registered
4. Check "Manifest" - should show all properties
5. Click "Add to Home Screen" from menu
6. Test offline: DevTools > Network > Offline checkbox

#### iOS (Safari)

1. Open in Safari (not Chrome)
2. Tap Share button
3. Scroll down and tap "Add to Home Screen"
4. Test offline: Settings > Airplane Mode

#### Desktop (Chrome)

1. Open in Chrome
2. Click install icon in address bar
3. Or: Settings > Install app
4. Test in standalone window

### Automated Testing

#### PWA Audit

```bash
# Using Lighthouse CI
npm install -g @lhci/cli

# Run audit
lhci autorun --collect.url=https://your-app-url
```

#### Service Worker Testing

```javascript
// sw-test.js
describe('Service Worker', () => {
  it('should register successfully', async () => {
    const registration = await navigator.serviceWorker.register('/service-worker.js');
    expect(registration.active).toBeTruthy();
  });

  it('should cache static assets', async () => {
    const cache = await caches.open('ai-ambassador-v1.0.0');
    const cachedResponse = await cache.match('/');
    expect(cachedResponse).toBeTruthy();
  });

  it('should handle offline requests', async () => {
    // Simulate offline
    await page.setOfflineMode(true);

    const response = await page.goto('https://your-app-url');
    expect(response.status()).toBe(200);
  });
});
```

### Testing Checklist

- [ ] Service worker registers successfully
- [ ] App installs on Android (Chrome)
- [ ] App installs on iOS (Safari)
- [ ] App installs on desktop (Chrome/Edge)
- [ ] Offline mode works (cached content loads)
- [ ] Messages queue when offline
- [ ] Messages sync when back online
- [ ] Push notifications work
- [ ] Notification permission prompt shows
- [ ] Notification click opens correct page
- [ ] Pull-to-refresh updates content
- [ ] Voice input works (if supported)
- [ ] Image sharing works
- [ ] Location sharing works (with permission)
- [ ] Haptic feedback works (on supported devices)
- [ ] App badge updates (if supported)
- [ ] Lighthouse PWA score: 100
- [ ] Lighthouse Performance score: 90+
- [ ] Works on 3G (< 3s load time)
- [ ] Touch targets are 44x44px minimum
- [ ] No layout shift (CLS < 0.1)

---

## Deployment

### Production Deployment

#### 1. Build Assets

```bash
# Optimize images
for file in icons/*.png; do
  pngquant --quality=80-100 --ext .png --force "$file"
done

# Minify JavaScript
npx terser scripts/mobile-app.js -o scripts/mobile-app.min.js --compress --mangle
npx terser scripts/offline-queue.js -o scripts/offline-queue.min.js --compress --mangle
npx terser scripts/push-notifications.js -o scripts/push-notifications.min.js --compress --mangle

# Update HTML to use minified files
sed -i 's/mobile-app.js/mobile-app.min.js/g' mobile-chat.html
```

#### 2. Deploy to Azure

```bash
# Deploy Azure Functions
cd Copilot-Agent-365-main
func azure functionapp publish <function-app-name>

# Deploy static files to Azure Storage (Static Website)
az storage blob upload-batch \
  --account-name <storage-account> \
  --destination '$web' \
  --source . \
  --pattern '*.{html,js,json,css,png,jpg,svg,webp}'
```

#### 3. Configure CDN (Optional)

```bash
# Create Azure CDN
az cdn profile create \
  --resource-group aibast-prod-rg \
  --name ai-ambassador-cdn

az cdn endpoint create \
  --resource-group aibast-prod-rg \
  --profile-name ai-ambassador-cdn \
  --name ai-ambassadors \
  --origin <storage-account>.blob.core.windows.net
```

#### 4. Update URLs

Update all hardcoded URLs to production:
- API endpoints in `mobile-app.js`
- Icon paths in `manifest.json`
- Start URL in `manifest.json`

#### 5. Test Production

```bash
# Run Lighthouse on production
lighthouse https://ai-ambassadors.app \
  --view \
  --chrome-flags="--headless"

# Check service worker
curl https://ai-ambassadors.app/service-worker.js

# Check manifest
curl https://ai-ambassadors.app/manifest.json
```

### HTTPS Setup

PWAs require HTTPS. Azure provides this automatically, but for custom domains:

```bash
# Using Let's Encrypt with Azure App Service
az webapp config ssl bind \
  --resource-group aibast-prod-rg \
  --name <app-name> \
  --certificate-thumbprint <thumbprint> \
  --ssl-type SNI
```

### Development with HTTPS

**Option 1: localhost (automatically secure)**
```bash
# Start local server
python -m http.server 8080
# Access at: http://localhost:8080
```

**Option 2: ngrok**
```bash
# Install ngrok
npm install -g ngrok

# Start tunnel
ngrok http 8080

# Access at: https://xyz123.ngrok.io
```

---

## Troubleshooting

### Service Worker Not Registering

**Symptoms:**
- "Service worker registration failed" error
- App doesn't work offline

**Solutions:**
1. **Check HTTPS**: Service workers require HTTPS (or localhost)
   ```javascript
   console.log('Is secure context:', window.isSecureContext);
   ```

2. **Check Path**: Service worker must be at root or higher than pages
   ```javascript
   // Correct
   navigator.serviceWorker.register('/service-worker.js');

   // Wrong (if pages are at root)
   navigator.serviceWorker.register('/js/service-worker.js');
   ```

3. **Check MIME Type**: Must be served as `text/javascript`
   ```bash
   # Azure Static Web App - web.config
   <staticContent>
     <mimeMap fileExtension=".js" mimeType="text/javascript" />
   </staticContent>
   ```

4. **Clear Cache**: Hard refresh (Ctrl+Shift+R)

### App Not Installing

**Symptoms:**
- No install prompt
- Install button doesn't work

**Solutions:**
1. **Check Manifest**: Must be valid JSON
   ```bash
   # Validate manifest
   curl https://your-app-url/manifest.json | python -m json.tool
   ```

2. **Check Icons**: Must have at least 192x192 and 512x512
   ```bash
   ls -lh icons/icon-*.png
   ```

3. **Check Installability**:
   - Open DevTools > Application > Manifest
   - Look for errors
   - Check "Add to home screen" section

4. **iOS Requirements**:
   - Must add apple-touch-icon
   - Must have apple-mobile-web-app-capable meta tag
   - No automatic install prompt (manual only)

### Push Notifications Not Working

**Symptoms:**
- Permission granted but no notifications
- Subscription fails

**Solutions:**
1. **Check Permission**:
   ```javascript
   console.log('Permission:', Notification.permission);
   ```

2. **Check Subscription**:
   ```javascript
   const sub = await registration.pushManager.getSubscription();
   console.log('Subscription:', sub);
   ```

3. **Check VAPID Keys**:
   - Must be valid base64
   - Public key in client
   - Private key in server
   - Subject must be mailto: or https:

4. **Test Notification**:
   ```javascript
   // Show local notification
   registration.showNotification('Test', {
     body: 'This is a test'
   });
   ```

5. **Check Browser Support**:
   ```javascript
   console.log('Push supported:', 'PushManager' in window);
   console.log('Notification supported:', 'Notification' in window);
   ```

### Offline Mode Not Working

**Symptoms:**
- App shows error when offline
- Cached content not loading

**Solutions:**
1. **Check Cache**:
   ```javascript
   // List all caches
   const cacheNames = await caches.keys();
   console.log('Caches:', cacheNames);

   // Check specific cache
   const cache = await caches.open('ai-ambassador-v1.0.0');
   const cachedUrls = await cache.keys();
   console.log('Cached URLs:', cachedUrls.map(r => r.url));
   ```

2. **Check Service Worker**:
   ```javascript
   // Check if controlling page
   console.log('Controller:', navigator.serviceWorker.controller);
   ```

3. **Force Update**:
   ```javascript
   // Unregister and re-register
   const registrations = await navigator.serviceWorker.getRegistrations();
   for (const registration of registrations) {
     await registration.unregister();
   }
   window.location.reload();
   ```

4. **Check Network Fallback**:
   - Ensure offline.html is cached
   - Check fetch event handler

### Performance Issues

**Symptoms:**
- Slow load times
- Laggy interactions
- High memory usage

**Solutions:**
1. **Analyze Bundle Size**:
   ```bash
   # Check file sizes
   du -sh scripts/*.js

   # Analyze with webpack-bundle-analyzer (if using webpack)
   npm install -D webpack-bundle-analyzer
   ```

2. **Enable Compression**:
   ```javascript
   // Azure Static Web App - staticwebapp.config.json
   {
     "responseOverrides": {
       "200": {
         "headers": {
           "Content-Encoding": "gzip"
         }
       }
     }
   }
   ```

3. **Optimize Images**:
   ```bash
   # Compress with pngquant
   pngquant --quality=80-100 icons/*.png

   # Convert to WebP
   for file in icons/*.png; do
     cwebp -q 80 "$file" -o "${file%.png}.webp"
   done
   ```

4. **Profile Performance**:
   - Open DevTools > Performance
   - Record page load
   - Look for long tasks (> 50ms)
   - Optimize bottlenecks

### iOS-Specific Issues

**Add to Home Screen Not Working:**
1. Must use Safari (not Chrome/Firefox)
2. Must be on actual device (not simulator)
3. Must have valid apple-touch-icon
4. Check meta tags

**Splash Screen Not Showing:**
1. Add apple-touch-startup-image
2. Multiple sizes for different devices

**Status Bar Issues:**
1. Use `viewport-fit=cover` for notch support
2. Use `safe-area-inset` CSS variables
3. Set status bar style in meta tag

---

## Resources

### Documentation

- [MDN - Progressive Web Apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [Google - PWA Checklist](https://web.dev/pwa-checklist/)
- [Web.dev - Workbox](https://developers.google.com/web/tools/workbox)
- [Push API Specification](https://www.w3.org/TR/push-api/)

### Tools

- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [PWA Builder](https://www.pwabuilder.com/)
- [Maskable.app](https://maskable.app/) - Test maskable icons
- [Web Push Testing](https://tests.peter.sh/notification-generator/)

### Testing Services

- [BrowserStack](https://www.browserstack.com/) - Real device testing
- [LambdaTest](https://www.lambdatest.com/) - Cross-browser testing
- [Sauce Labs](https://saucelabs.com/) - Automated testing

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-repo/issues
- Email: support@ai-ambassadors.app
- Documentation: /docs/pwa

---

## License

Copyright 2025 AI Ambassador Platform. All rights reserved.
