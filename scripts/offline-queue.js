// Offline Queue Manager
// Handles queuing and syncing of messages when offline

class OfflineQueue {
  constructor() {
    this.dbName = 'AIAmbassadorDB';
    this.dbVersion = 1;
    this.queueStoreName = 'queue';
    this.syncInProgress = false;

    this.init();
  }

  async init() {
    console.log('[OfflineQueue] Initializing...');

    // Listen for online event
    window.addEventListener('online', () => {
      console.log('[OfflineQueue] Network restored, syncing...');
      this.sync();
    });

    // Listen for service worker messages
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data.type === 'SYNC_COMPLETE') {
          this.handleSyncComplete(event.data);
        }
      });
    }

    console.log('[OfflineQueue] Initialized');
  }

  async openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        console.error('[OfflineQueue] Database error:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Create queue store if it doesn't exist
        if (!db.objectStoreNames.contains(this.queueStoreName)) {
          const store = db.createObjectStore(this.queueStoreName, {
            keyPath: 'id',
            autoIncrement: true
          });

          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('status', 'status', { unique: false });
          store.createIndex('retryCount', 'retryCount', { unique: false });

          console.log('[OfflineQueue] Queue store created');
        }

        // Create conversations store if it doesn't exist
        if (!db.objectStoreNames.contains('conversations')) {
          const store = db.createObjectStore('conversations', {
            keyPath: 'id',
            autoIncrement: true
          });

          store.createIndex('ambassadorId', 'ambassadorId', { unique: false });
          store.createIndex('timestamp', 'timestamp', { unique: false });

          console.log('[OfflineQueue] Conversations store created');
        }
      };
    });
  }

  async queueMessage(message, userId, conversationHistory = []) {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(this.queueStoreName, 'readwrite');
      const store = tx.objectStore(this.queueStoreName);

      const queueItem = {
        url: '/api/businessinsightbot_function',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_input: message,
          conversation_history: conversationHistory,
          user_guid: userId
        }),
        message: message,
        timestamp: Date.now(),
        status: 'pending',
        retryCount: 0,
        maxRetries: 3
      };

      const request = store.add(queueItem);

      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          console.log('[OfflineQueue] Message queued:', request.result);
          resolve(request.result);
        };

        request.onerror = () => {
          console.error('[OfflineQueue] Failed to queue message:', request.error);
          reject(request.error);
        };
      });
    } catch (error) {
      console.error('[OfflineQueue] Queue error:', error);
      throw error;
    }
  }

  async getQueuedMessages() {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(this.queueStoreName, 'readonly');
      const store = tx.objectStore(this.queueStoreName);
      const index = store.index('status');

      const request = index.getAll('pending');

      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          const messages = request.result;
          console.log('[OfflineQueue] Found queued messages:', messages.length);
          resolve(messages);
        };

        request.onerror = () => {
          console.error('[OfflineQueue] Failed to get queued messages:', request.error);
          reject(request.error);
        };
      });
    } catch (error) {
      console.error('[OfflineQueue] Get queue error:', error);
      return [];
    }
  }

  async sync() {
    if (this.syncInProgress) {
      console.log('[OfflineQueue] Sync already in progress');
      return;
    }

    if (!navigator.onLine) {
      console.log('[OfflineQueue] Cannot sync - offline');
      return;
    }

    this.syncInProgress = true;

    try {
      const messages = await this.getQueuedMessages();

      if (messages.length === 0) {
        console.log('[OfflineQueue] No messages to sync');
        this.syncInProgress = false;
        return;
      }

      console.log('[OfflineQueue] Syncing', messages.length, 'messages...');

      const results = {
        success: 0,
        failed: 0,
        total: messages.length
      };

      for (const message of messages) {
        const success = await this.sendQueuedMessage(message);

        if (success) {
          results.success++;
          await this.removeFromQueue(message.id);
        } else {
          results.failed++;

          if (message.retryCount >= message.maxRetries) {
            console.error('[OfflineQueue] Max retries reached for message:', message.id);
            await this.markAsFailed(message.id);
          } else {
            await this.incrementRetryCount(message.id);
          }
        }
      }

      console.log('[OfflineQueue] Sync complete:', results);

      // Notify app
      if (window.app && results.success > 0) {
        window.app.showNotification(`${results.success} message(s) sent`);
      }

      // Trigger background sync for remaining messages
      if (results.failed > 0 && 'serviceWorker' in navigator && 'sync' in self.registration) {
        try {
          const registration = await navigator.serviceWorker.ready;
          await registration.sync.register('sync-messages');
          console.log('[OfflineQueue] Background sync registered');
        } catch (error) {
          console.error('[OfflineQueue] Background sync registration failed:', error);
        }
      }
    } catch (error) {
      console.error('[OfflineQueue] Sync error:', error);
    } finally {
      this.syncInProgress = false;
    }
  }

  async sendQueuedMessage(queueItem) {
    try {
      console.log('[OfflineQueue] Sending queued message:', queueItem.id);

      const response = await fetch(queueItem.url, {
        method: queueItem.method,
        headers: queueItem.headers,
        body: queueItem.body,
        timeout: 10000
      });

      if (response.ok) {
        console.log('[OfflineQueue] Message sent successfully:', queueItem.id);

        // Parse response and save to conversation history
        try {
          const data = await response.json();
          const assistantMessage = data.response || data.message;

          if (assistantMessage && window.app) {
            // Add assistant response to UI
            const [formattedResponse] = assistantMessage.split('|||VOICE|||');
            window.app.addMessageToUI('assistant', formattedResponse, Date.now());

            // Update conversation history
            window.app.conversationHistory.push({
              role: 'assistant',
              content: formattedResponse
            });

            await window.app.saveConversation();
          }
        } catch (parseError) {
          console.error('[OfflineQueue] Failed to parse response:', parseError);
        }

        return true;
      } else {
        console.error('[OfflineQueue] Message send failed:', response.status);
        return false;
      }
    } catch (error) {
      console.error('[OfflineQueue] Send error:', error);
      return false;
    }
  }

  async removeFromQueue(messageId) {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(this.queueStoreName, 'readwrite');
      const store = tx.objectStore(this.queueStoreName);

      const request = store.delete(messageId);

      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          console.log('[OfflineQueue] Message removed from queue:', messageId);
          resolve();
        };

        request.onerror = () => {
          console.error('[OfflineQueue] Failed to remove message:', request.error);
          reject(request.error);
        };
      });
    } catch (error) {
      console.error('[OfflineQueue] Remove error:', error);
    }
  }

  async incrementRetryCount(messageId) {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(this.queueStoreName, 'readwrite');
      const store = tx.objectStore(this.queueStoreName);

      const getRequest = store.get(messageId);

      return new Promise((resolve, reject) => {
        getRequest.onsuccess = () => {
          const message = getRequest.result;
          if (message) {
            message.retryCount = (message.retryCount || 0) + 1;
            message.lastRetry = Date.now();

            const putRequest = store.put(message);

            putRequest.onsuccess = () => {
              console.log('[OfflineQueue] Retry count incremented:', messageId, message.retryCount);
              resolve();
            };

            putRequest.onerror = () => {
              console.error('[OfflineQueue] Failed to increment retry count:', putRequest.error);
              reject(putRequest.error);
            };
          } else {
            resolve();
          }
        };

        getRequest.onerror = () => {
          console.error('[OfflineQueue] Failed to get message:', getRequest.error);
          reject(getRequest.error);
        };
      });
    } catch (error) {
      console.error('[OfflineQueue] Increment retry error:', error);
    }
  }

  async markAsFailed(messageId) {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(this.queueStoreName, 'readwrite');
      const store = tx.objectStore(this.queueStoreName);

      const getRequest = store.get(messageId);

      return new Promise((resolve, reject) => {
        getRequest.onsuccess = () => {
          const message = getRequest.result;
          if (message) {
            message.status = 'failed';
            message.failedAt = Date.now();

            const putRequest = store.put(message);

            putRequest.onsuccess = () => {
              console.log('[OfflineQueue] Message marked as failed:', messageId);
              resolve();
            };

            putRequest.onerror = () => {
              console.error('[OfflineQueue] Failed to mark as failed:', putRequest.error);
              reject(putRequest.error);
            };
          } else {
            resolve();
          }
        };

        getRequest.onerror = () => {
          console.error('[OfflineQueue] Failed to get message:', getRequest.error);
          reject(getRequest.error);
        };
      });
    } catch (error) {
      console.error('[OfflineQueue] Mark failed error:', error);
    }
  }

  async getFailedMessages() {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(this.queueStoreName, 'readonly');
      const store = tx.objectStore(this.queueStoreName);
      const index = store.index('status');

      const request = index.getAll('failed');

      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          resolve(request.result);
        };

        request.onerror = () => {
          reject(request.error);
        };
      });
    } catch (error) {
      console.error('[OfflineQueue] Get failed messages error:', error);
      return [];
    }
  }

  async clearQueue() {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(this.queueStoreName, 'readwrite');
      const store = tx.objectStore(this.queueStoreName);

      const request = store.clear();

      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          console.log('[OfflineQueue] Queue cleared');
          resolve();
        };

        request.onerror = () => {
          console.error('[OfflineQueue] Failed to clear queue:', request.error);
          reject(request.error);
        };
      });
    } catch (error) {
      console.error('[OfflineQueue] Clear queue error:', error);
    }
  }

  async getQueueStats() {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction(this.queueStoreName, 'readonly');
      const store = tx.objectStore(this.queueStoreName);

      const allRequest = store.getAll();

      return new Promise((resolve, reject) => {
        allRequest.onsuccess = () => {
          const messages = allRequest.result;

          const stats = {
            total: messages.length,
            pending: messages.filter(m => m.status === 'pending').length,
            failed: messages.filter(m => m.status === 'failed').length,
            oldestTimestamp: messages.length > 0 ?
              Math.min(...messages.map(m => m.timestamp)) : null
          };

          resolve(stats);
        };

        allRequest.onerror = () => {
          reject(allRequest.error);
        };
      });
    } catch (error) {
      console.error('[OfflineQueue] Get stats error:', error);
      return {
        total: 0,
        pending: 0,
        failed: 0,
        oldestTimestamp: null
      };
    }
  }

  handleSyncComplete(data) {
    console.log('[OfflineQueue] Sync complete notification:', data);

    if (window.app) {
      window.app.loadConversationHistory();
    }
  }
}

// Initialize offline queue
window.OfflineQueue = OfflineQueue;

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.offlineQueue = new OfflineQueue();
  });
} else {
  window.offlineQueue = new OfflineQueue();
}
