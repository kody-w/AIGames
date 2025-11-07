// Push Notifications Manager
// Handles push notification subscription and management

class PushNotificationManager {
  constructor() {
    this.swRegistration = null;
    this.isSubscribed = false;
    this.applicationServerKey = null; // Set this to your VAPID public key

    this.init();
  }

  async init() {
    console.log('[PushNotifications] Initializing...');

    // Check for service worker and push support
    if (!('serviceWorker' in navigator)) {
      console.warn('[PushNotifications] Service workers not supported');
      return;
    }

    if (!('PushManager' in window)) {
      console.warn('[PushNotifications] Push notifications not supported');
      return;
    }

    try {
      // Wait for service worker to be ready
      this.swRegistration = await navigator.serviceWorker.ready;
      console.log('[PushNotifications] Service worker ready');

      // Check existing subscription
      await this.checkSubscription();

      console.log('[PushNotifications] Initialized');
    } catch (error) {
      console.error('[PushNotifications] Initialization failed:', error);
    }
  }

  async checkSubscription() {
    try {
      const subscription = await this.swRegistration.pushManager.getSubscription();
      this.isSubscribed = subscription !== null;

      console.log('[PushNotifications] Subscription status:', this.isSubscribed);

      if (subscription) {
        console.log('[PushNotifications] Existing subscription:', subscription.endpoint);
        // Update UI or send subscription to server
        this.updateSubscriptionOnServer(subscription);
      }

      return this.isSubscribed;
    } catch (error) {
      console.error('[PushNotifications] Check subscription failed:', error);
      return false;
    }
  }

  async requestPermission() {
    console.log('[PushNotifications] Requesting permission...');

    try {
      const permission = await Notification.requestPermission();

      console.log('[PushNotifications] Permission:', permission);

      if (permission === 'granted') {
        await this.subscribeUser();
        return true;
      } else if (permission === 'denied') {
        console.warn('[PushNotifications] Permission denied');
        return false;
      } else {
        console.log('[PushNotifications] Permission dismissed');
        return false;
      }
    } catch (error) {
      console.error('[PushNotifications] Permission request failed:', error);
      return false;
    }
  }

  async subscribeUser() {
    try {
      console.log('[PushNotifications] Subscribing user...');

      // Convert application server key
      const applicationServerKey = this.urlBase64ToUint8Array(
        this.applicationServerKey || this.getDefaultVapidKey()
      );

      const subscription = await this.swRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
      });

      console.log('[PushNotifications] User subscribed:', subscription.endpoint);

      this.isSubscribed = true;

      // Send subscription to server
      await this.updateSubscriptionOnServer(subscription);

      // Show confirmation
      this.showLocalNotification(
        'Notifications Enabled',
        'You will receive notifications from your AI Ambassadors'
      );

      return subscription;
    } catch (error) {
      console.error('[PushNotifications] Subscription failed:', error);
      throw error;
    }
  }

  async unsubscribeUser() {
    try {
      console.log('[PushNotifications] Unsubscribing user...');

      const subscription = await this.swRegistration.pushManager.getSubscription();

      if (subscription) {
        await subscription.unsubscribe();
        console.log('[PushNotifications] User unsubscribed');

        this.isSubscribed = false;

        // Remove subscription from server
        await this.deleteSubscriptionFromServer(subscription);

        return true;
      }

      return false;
    } catch (error) {
      console.error('[PushNotifications] Unsubscribe failed:', error);
      return false;
    }
  }

  async updateSubscriptionOnServer(subscription) {
    try {
      const userId = localStorage.getItem('userId');
      const ambassadorId = localStorage.getItem('currentAmbassador');

      const response = await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          subscription: subscription.toJSON(),
          userId: userId,
          ambassadorId: ambassadorId,
          timestamp: Date.now()
        })
      });

      if (response.ok) {
        console.log('[PushNotifications] Subscription saved to server');
        return true;
      } else {
        console.error('[PushNotifications] Failed to save subscription:', response.status);
        return false;
      }
    } catch (error) {
      console.error('[PushNotifications] Update subscription error:', error);
      return false;
    }
  }

  async deleteSubscriptionFromServer(subscription) {
    try {
      const response = await fetch('/api/push/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint
        })
      });

      if (response.ok) {
        console.log('[PushNotifications] Subscription removed from server');
        return true;
      } else {
        console.error('[PushNotifications] Failed to remove subscription:', response.status);
        return false;
      }
    } catch (error) {
      console.error('[PushNotifications] Delete subscription error:', error);
      return false;
    }
  }

  async showLocalNotification(title, body, options = {}) {
    if (!('Notification' in window)) {
      console.warn('[PushNotifications] Notifications not supported');
      return;
    }

    if (Notification.permission !== 'granted') {
      console.warn('[PushNotifications] Notification permission not granted');
      return;
    }

    try {
      const notificationOptions = {
        body: body,
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        tag: 'ambassador-notification',
        requireInteraction: false,
        ...options
      };

      await this.swRegistration.showNotification(title, notificationOptions);

      console.log('[PushNotifications] Local notification shown');
    } catch (error) {
      console.error('[PushNotifications] Show notification failed:', error);
    }
  }

  async testNotification() {
    console.log('[PushNotifications] Testing notification...');

    await this.showLocalNotification(
      'Test Notification',
      'This is a test notification from AI Ambassadors',
      {
        actions: [
          { action: 'open', title: 'Open', icon: '/icons/open-icon.png' },
          { action: 'dismiss', title: 'Dismiss', icon: '/icons/close-icon.png' }
        ],
        data: {
          url: '/mobile-chat.html',
          timestamp: Date.now()
        }
      }
    );
  }

  // Helper functions
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
  }

  getDefaultVapidKey() {
    // This should be replaced with your actual VAPID public key
    // Generate one using: npx web-push generate-vapid-keys
    return 'BEl62iUYgUivxIkv69yViEuiBIa-Ib37J8Aa4K7MLW0cYu0k3bR_RvGn5FCK6s3H6OqYzqYqHvY0bx9Lx8qEDYQ';
  }

  // Notification preferences
  async getNotificationPreferences() {
    const prefs = localStorage.getItem('notificationPreferences');
    return prefs ? JSON.parse(prefs) : this.getDefaultPreferences();
  }

  async setNotificationPreferences(preferences) {
    localStorage.setItem('notificationPreferences', JSON.stringify(preferences));
    console.log('[PushNotifications] Preferences saved:', preferences);
  }

  getDefaultPreferences() {
    return {
      enabled: false,
      newMessages: true,
      ambassadorUpdates: true,
      nearbyAmbassadors: true,
      quietHours: {
        enabled: false,
        start: '22:00',
        end: '08:00'
      },
      sound: true,
      vibration: true
    };
  }

  async isInQuietHours() {
    const prefs = await this.getNotificationPreferences();

    if (!prefs.quietHours.enabled) {
      return false;
    }

    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();

    const [startHour, startMin] = prefs.quietHours.start.split(':').map(Number);
    const [endHour, endMin] = prefs.quietHours.end.split(':').map(Number);

    const startTime = startHour * 60 + startMin;
    const endTime = endHour * 60 + endMin;

    if (startTime < endTime) {
      return currentTime >= startTime && currentTime < endTime;
    } else {
      return currentTime >= startTime || currentTime < endTime;
    }
  }

  // UI helpers
  async showNotificationPrompt() {
    if (Notification.permission === 'granted') {
      console.log('[PushNotifications] Already has permission');
      return true;
    }

    if (Notification.permission === 'denied') {
      console.log('[PushNotifications] Permission denied, showing instructions');
      this.showPermissionInstructions();
      return false;
    }

    // Show custom prompt
    return new Promise((resolve) => {
      const prompt = document.createElement('div');
      prompt.className = 'notification-prompt';
      prompt.innerHTML = `
        <div class="notification-prompt-content">
          <div class="notification-prompt-icon">🔔</div>
          <div class="notification-prompt-text">
            <h3>Stay Connected</h3>
            <p>Get notified when your AI Ambassadors send you messages</p>
          </div>
          <div class="notification-prompt-actions">
            <button class="enable-notifications">Enable Notifications</button>
            <button class="dismiss-notifications">Not Now</button>
          </div>
        </div>
      `;

      // Add styles
      const style = document.createElement('style');
      style.textContent = `
        .notification-prompt {
          position: fixed;
          top: 20px;
          left: 50%;
          transform: translateX(-50%);
          background: white;
          border-radius: 12px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
          padding: 20px;
          z-index: 10000;
          max-width: 400px;
          width: calc(100% - 40px);
          animation: slideDown 0.3s ease-out;
        }

        @keyframes slideDown {
          from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
          to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }

        .notification-prompt-content {
          text-align: center;
        }

        .notification-prompt-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .notification-prompt-text h3 {
          font-size: 18px;
          margin-bottom: 8px;
          color: #111827;
        }

        .notification-prompt-text p {
          font-size: 14px;
          color: #6b7280;
          margin-bottom: 20px;
        }

        .notification-prompt-actions {
          display: flex;
          gap: 8px;
        }

        .enable-notifications {
          flex: 1;
          background: #6366f1;
          color: white;
          border: none;
          padding: 12px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
        }

        .dismiss-notifications {
          flex: 1;
          background: #f3f4f6;
          color: #111827;
          border: none;
          padding: 12px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
        }
      `;

      document.head.appendChild(style);
      document.body.appendChild(prompt);

      // Handle enable
      prompt.querySelector('.enable-notifications').addEventListener('click', async () => {
        prompt.remove();
        const granted = await this.requestPermission();
        resolve(granted);
      });

      // Handle dismiss
      prompt.querySelector('.dismiss-notifications').addEventListener('click', () => {
        prompt.remove();
        resolve(false);
      });

      // Auto-dismiss after 10 seconds
      setTimeout(() => {
        if (document.body.contains(prompt)) {
          prompt.remove();
          resolve(false);
        }
      }, 10000);
    });
  }

  showPermissionInstructions() {
    alert(
      'Notifications are blocked.\n\n' +
      'To enable notifications:\n' +
      '1. Click the lock icon in the address bar\n' +
      '2. Find "Notifications" in the permissions list\n' +
      '3. Change it to "Allow"'
    );
  }
}

// Initialize push notification manager
window.PushNotificationManager = PushNotificationManager;

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.pushNotifications = new PushNotificationManager();
  });
} else {
  window.pushNotifications = new PushNotificationManager();
}
