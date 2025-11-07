// Mobile App - AI Ambassador Platform PWA
// Main application logic

class MobileApp {
  constructor() {
    this.ambassadorId = null;
    this.userId = null;
    this.conversationHistory = [];
    this.isOnline = navigator.onLine;
    this.deferredPrompt = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.recordingStartTime = null;
    this.recordingInterval = null;
    this.touchStartY = 0;
    this.isPulling = false;

    this.init();
  }

  async init() {
    console.log('[MobileApp] Initializing...');

    // Initialize service worker
    await this.registerServiceWorker();

    // Set up event listeners
    this.setupEventListeners();

    // Load ambassador from URL or storage
    await this.loadAmbassador();

    // Check for install prompt
    this.checkInstallPrompt();

    // Initialize offline queue
    if (window.OfflineQueue) {
      this.offlineQueue = new OfflineQueue();
    }

    // Auto-adjust textarea height
    this.setupTextareaAutoResize();

    // Update online/offline status
    this.updateOnlineStatus();

    console.log('[MobileApp] Initialized');
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/service-worker.js');
        console.log('[MobileApp] Service Worker registered:', registration);

        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              this.showUpdateNotification();
            }
          });
        });
      } catch (error) {
        console.error('[MobileApp] Service Worker registration failed:', error);
      }
    }
  }

  setupEventListeners() {
    // Online/Offline events
    window.addEventListener('online', () => this.handleOnlineStatusChange(true));
    window.addEventListener('offline', () => this.handleOnlineStatusChange(false));

    // Back button
    document.getElementById('backButton').addEventListener('click', () => this.goBack());

    // Info button
    document.getElementById('infoButton').addEventListener('click', () => this.showAmbassadorInfo());

    // Menu button
    document.getElementById('menuButton').addEventListener('click', () => this.showMenu());

    // Message input
    const messageInput = document.getElementById('messageInput');
    messageInput.addEventListener('input', () => this.handleInputChange());
    messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));

    // Send button
    document.getElementById('sendButton').addEventListener('click', () => this.sendMessage());

    // Quick actions
    document.querySelectorAll('.quick-action').forEach(button => {
      button.addEventListener('click', (e) => this.handleQuickAction(e.target.textContent));
    });

    // Attach button
    document.getElementById('attachButton').addEventListener('click', () => this.handleAttach());
    document.getElementById('imageInput').addEventListener('change', (e) => this.handleImageSelect(e));

    // Voice button
    document.getElementById('voiceButton').addEventListener('click', () => this.handleVoiceInput());
    document.getElementById('cancelRecording').addEventListener('click', () => this.cancelRecording());

    // Location button
    document.getElementById('locationButton').addEventListener('click', () => this.handleLocationShare());

    // Remove image
    document.getElementById('removeImage').addEventListener('click', () => this.removeImage());

    // Install prompt
    document.getElementById('installButton').addEventListener('click', () => this.installApp());
    document.getElementById('dismissButton').addEventListener('click', () => this.dismissInstallPrompt());

    // Before install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallPrompt();
    });

    // App installed
    window.addEventListener('appinstalled', () => {
      console.log('[MobileApp] App installed');
      this.deferredPrompt = null;
      this.hideInstallPrompt();
    });

    // Pull to refresh
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.addEventListener('touchstart', (e) => this.handleTouchStart(e));
    chatContainer.addEventListener('touchmove', (e) => this.handleTouchMove(e));
    chatContainer.addEventListener('touchend', () => this.handleTouchEnd());

    // Service worker messages
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        this.handleServiceWorkerMessage(event.data);
      });
    }

    // Haptic feedback for all buttons
    document.querySelectorAll('.haptic-target').forEach(element => {
      element.addEventListener('click', () => this.hapticFeedback());
    });

    // Visibility change - sync when app comes back
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.isOnline) {
        this.syncMessages();
      }
    });
  }

  handleOnlineStatusChange(isOnline) {
    this.isOnline = isOnline;
    this.updateOnlineStatus();

    if (isOnline) {
      console.log('[MobileApp] Back online, syncing messages...');
      this.syncMessages();
    }
  }

  updateOnlineStatus() {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const offlineBanner = document.getElementById('offlineBanner');

    if (this.isOnline) {
      statusIndicator.classList.remove('offline');
      statusText.textContent = 'Online';
      offlineBanner.classList.remove('show');
    } else {
      statusIndicator.classList.add('offline');
      statusText.textContent = 'Offline';
      offlineBanner.classList.add('show');
    }
  }

  async loadAmbassador() {
    // Get ambassador ID from URL or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    this.ambassadorId = urlParams.get('ambassador') || localStorage.getItem('currentAmbassador') || 'creative-001';
    this.userId = localStorage.getItem('userId') || this.generateUserId();

    // Save to localStorage
    localStorage.setItem('currentAmbassador', this.ambassadorId);
    localStorage.setItem('userId', this.userId);

    // Load ambassador config
    try {
      const response = await fetch(`/api/ambassador_entry?ambassador_id=${this.ambassadorId}`);
      if (response.ok) {
        const data = await response.json();
        this.updateAmbassadorUI(data.ambassador);
      }
    } catch (error) {
      console.error('[MobileApp] Failed to load ambassador:', error);
    }

    // Load conversation history from cache
    this.loadConversationHistory();
  }

  updateAmbassadorUI(ambassador) {
    document.getElementById('ambassadorAvatar').textContent = ambassador.avatar?.value || '🎨';
    document.getElementById('ambassadorName').textContent = ambassador.name || 'Ambassador';
    document.title = `${ambassador.name} - AI Ambassador`;
  }

  generateUserId() {
    return 'user_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }

  async loadConversationHistory() {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction('conversations', 'readonly');
      const store = tx.objectStore('conversations');
      const index = store.index('ambassadorId');
      const messages = await index.getAll(this.ambassadorId);

      this.conversationHistory = messages.sort((a, b) => a.timestamp - b.timestamp);
      this.renderConversationHistory();
    } catch (error) {
      console.error('[MobileApp] Failed to load conversation:', error);
    }
  }

  renderConversationHistory() {
    const chatContainer = document.getElementById('chatContainer');
    // Keep only the welcome message and typing indicator
    const welcomeMessage = chatContainer.children[0];
    const typingIndicator = chatContainer.children[1];

    chatContainer.innerHTML = '';
    chatContainer.appendChild(welcomeMessage);

    this.conversationHistory.forEach(msg => {
      this.addMessageToUI(msg.role, msg.content, msg.timestamp, msg.queued);
    });

    chatContainer.appendChild(typingIndicator);
    this.scrollToBottom();
  }

  handleInputChange() {
    const input = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');

    sendButton.disabled = !input.value.trim();
  }

  handleKeyDown(e) {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  }

  async sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    // Add to UI immediately
    this.addMessageToUI('user', message, Date.now());

    // Clear input
    input.value = '';
    this.handleInputChange();

    // Save to history
    this.conversationHistory.push({
      role: 'user',
      content: message
    });

    // Show typing indicator
    this.showTypingIndicator();

    try {
      // Send to API
      const response = await fetch('/api/businessinsightbot_function', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_input: message,
          conversation_history: this.conversationHistory,
          user_guid: this.userId
        })
      });

      this.hideTypingIndicator();

      if (response.ok) {
        const data = await response.json();
        const assistantMessage = data.response || data.message || 'I received your message!';

        // Split by voice delimiter if present
        const [formattedResponse] = assistantMessage.split('|||VOICE|||');

        this.addMessageToUI('assistant', formattedResponse, Date.now());

        this.conversationHistory.push({
          role: 'assistant',
          content: formattedResponse
        });

        // Save conversation
        await this.saveConversation();
      } else if (response.status === 202) {
        // Message queued
        console.log('[MobileApp] Message queued for offline sync');
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error('[MobileApp] Send message failed:', error);
      this.hideTypingIndicator();

      // Queue message if offline
      if (!this.isOnline && this.offlineQueue) {
        await this.offlineQueue.queueMessage(message, this.userId, this.conversationHistory);
        this.showNotification('Message queued for when you\'re back online');
      } else {
        this.addMessageToUI('system', 'Failed to send message. Please try again.', Date.now());
      }
    }
  }

  addMessageToUI(role, content, timestamp, queued = false) {
    const chatContainer = document.getElementById('chatContainer');
    const typingIndicator = chatContainer.querySelector('.typing-indicator').parentElement;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    if (queued) messageDiv.classList.add('queued');

    const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (role === 'user') {
      messageDiv.innerHTML = `
        <div class="message-content">
          <div class="message-bubble">${this.escapeHtml(content)}</div>
          <div class="message-status">
            <span class="message-time">${time}</span>
            ${queued ? '<span>⏱ Queued</span>' : '<span>✓</span>'}
          </div>
        </div>
      `;
    } else if (role === 'assistant') {
      const avatar = document.getElementById('ambassadorAvatar').textContent;
      messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
          <div class="message-bubble">${this.formatMessage(content)}</div>
          <div class="message-time">${time}</div>
        </div>
      `;
    } else {
      messageDiv.innerHTML = `
        <div class="message-content">
          <div class="message-bubble" style="background: var(--warning-color); color: white;">
            ${this.escapeHtml(content)}
          </div>
        </div>
      `;
    }

    chatContainer.insertBefore(messageDiv, typingIndicator);
    this.scrollToBottom();
    this.hapticFeedback('light');
  }

  formatMessage(text) {
    // Basic markdown-style formatting
    text = this.escapeHtml(text);
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/\n/g, '<br>');
    return text;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  showTypingIndicator() {
    document.getElementById('typingIndicator').classList.add('show');
    this.scrollToBottom();
  }

  hideTypingIndicator() {
    document.getElementById('typingIndicator').classList.remove('show');
  }

  scrollToBottom() {
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  handleQuickAction(text) {
    const input = document.getElementById('messageInput');
    input.value = text;
    this.handleInputChange();
    this.sendMessage();

    // Hide quick actions after use
    document.getElementById('quickActions').style.display = 'none';
  }

  handleAttach() {
    document.getElementById('imageInput').click();
  }

  async handleImageSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (event) => {
      document.getElementById('previewImage').src = event.target.result;
      document.getElementById('imagePreview').classList.add('show');
    };
    reader.readAsDataURL(file);

    this.hapticFeedback();
  }

  removeImage() {
    document.getElementById('imagePreview').classList.remove('show');
    document.getElementById('imageInput').value = '';
    this.hapticFeedback();
  }

  async handleVoiceInput() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Voice input is not supported in your browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      console.log('[MobileApp] Voice recognition started');
      this.showVoiceRecording();
      this.hapticFeedback('medium');
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      document.getElementById('messageInput').value = transcript;
      this.handleInputChange();
      this.hideVoiceRecording();
    };

    recognition.onerror = (event) => {
      console.error('[MobileApp] Voice recognition error:', event.error);
      this.hideVoiceRecording();
    };

    recognition.onend = () => {
      console.log('[MobileApp] Voice recognition ended');
      this.hideVoiceRecording();
    };

    recognition.start();
  }

  showVoiceRecording() {
    document.getElementById('voiceRecording').classList.add('show');
    this.recordingStartTime = Date.now();
    this.recordingInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
      const minutes = Math.floor(elapsed / 60);
      const seconds = elapsed % 60;
      document.getElementById('recordingTime').textContent =
        `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
  }

  hideVoiceRecording() {
    document.getElementById('voiceRecording').classList.remove('show');
    if (this.recordingInterval) {
      clearInterval(this.recordingInterval);
      this.recordingInterval = null;
    }
  }

  cancelRecording() {
    this.hideVoiceRecording();
    this.hapticFeedback();
  }

  async handleLocationShare() {
    if (!('geolocation' in navigator)) {
      alert('Location sharing is not supported in your browser');
      return;
    }

    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
      });

      const { latitude, longitude } = position.coords;
      const locationMessage = `📍 My location: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;

      document.getElementById('messageInput').value = locationMessage;
      this.handleInputChange();
      this.hapticFeedback('medium');
    } catch (error) {
      console.error('[MobileApp] Location error:', error);
      alert('Unable to get your location');
    }
  }

  setupTextareaAutoResize() {
    const textarea = document.getElementById('messageInput');

    textarea.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
  }

  // Pull to refresh
  handleTouchStart(e) {
    const chatContainer = document.getElementById('chatContainer');
    if (chatContainer.scrollTop === 0) {
      this.touchStartY = e.touches[0].clientY;
    }
  }

  handleTouchMove(e) {
    if (!this.touchStartY) return;

    const touchY = e.touches[0].clientY;
    const pullDistance = touchY - this.touchStartY;

    if (pullDistance > 0 && pullDistance < 100) {
      this.isPulling = true;
      const pullToRefresh = document.getElementById('pullToRefresh');
      pullToRefresh.classList.add('pulling');
      pullToRefresh.style.transform = `translateY(${pullDistance}px)`;
      e.preventDefault();
    }
  }

  async handleTouchEnd() {
    if (!this.isPulling) return;

    const pullToRefresh = document.getElementById('pullToRefresh');
    const pullDistance = parseInt(pullToRefresh.style.transform.match(/\d+/)?.[0] || 0);

    if (pullDistance > 80) {
      pullToRefresh.classList.add('refreshing');
      pullToRefresh.querySelector('span:last-child').textContent = 'Refreshing...';

      await this.refresh();

      pullToRefresh.classList.remove('refreshing');
      pullToRefresh.querySelector('span:last-child').textContent = 'Pull to refresh';
    }

    pullToRefresh.classList.remove('pulling');
    pullToRefresh.style.transform = '';
    this.touchStartY = 0;
    this.isPulling = false;
  }

  async refresh() {
    console.log('[MobileApp] Refreshing...');
    await this.loadConversationHistory();
    await this.syncMessages();
    this.hapticFeedback('medium');

    // Simulate delay for better UX
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  async syncMessages() {
    if (this.offlineQueue) {
      await this.offlineQueue.sync();
    }
  }

  // Install prompt
  checkInstallPrompt() {
    // Don't show if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      console.log('[MobileApp] App is installed');
      return;
    }

    // Don't show if dismissed recently
    const dismissed = localStorage.getItem('installPromptDismissed');
    if (dismissed && Date.now() - parseInt(dismissed) < 7 * 24 * 60 * 60 * 1000) {
      return;
    }

    // Show after 30 seconds
    setTimeout(() => {
      if (this.deferredPrompt) {
        this.showInstallPrompt();
      }
    }, 30000);
  }

  showInstallPrompt() {
    document.getElementById('installPrompt').classList.add('show');
  }

  hideInstallPrompt() {
    document.getElementById('installPrompt').classList.remove('show');
  }

  async installApp() {
    if (!this.deferredPrompt) {
      // iOS instructions
      if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
        alert('To install:\n1. Tap the Share button\n2. Scroll down and tap "Add to Home Screen"');
      }
      return;
    }

    this.deferredPrompt.prompt();
    const { outcome } = await this.deferredPrompt.userChoice;

    console.log('[MobileApp] Install prompt outcome:', outcome);

    this.deferredPrompt = null;
    this.hideInstallPrompt();
    this.hapticFeedback('medium');
  }

  dismissInstallPrompt() {
    localStorage.setItem('installPromptDismissed', Date.now().toString());
    this.hideInstallPrompt();
    this.hapticFeedback();
  }

  showUpdateNotification() {
    const notification = confirm('A new version is available! Reload to update?');
    if (notification) {
      window.location.reload();
    }
  }

  // Database helpers
  async openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('AIAmbassadorDB', 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

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

  async saveConversation() {
    try {
      const db = await this.openDatabase();
      const tx = db.transaction('conversations', 'readwrite');
      const store = tx.objectStore('conversations');

      for (const msg of this.conversationHistory) {
        if (!msg.saved) {
          await store.add({
            ambassadorId: this.ambassadorId,
            role: msg.role,
            content: msg.content,
            timestamp: Date.now()
          });
          msg.saved = true;
        }
      }
    } catch (error) {
      console.error('[MobileApp] Failed to save conversation:', error);
    }
  }

  // Navigation
  goBack() {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = '/';
    }
  }

  showAmbassadorInfo() {
    alert(`Ambassador: ${document.getElementById('ambassadorName').textContent}\nID: ${this.ambassadorId}`);
  }

  showMenu() {
    // TODO: Implement full menu
    const options = [
      'Clear conversation',
      'Notification settings',
      'About'
    ];

    const choice = confirm('Menu:\n' + options.join('\n'));
    // TODO: Handle menu actions
  }

  // Haptic feedback
  hapticFeedback(type = 'light') {
    if ('vibrate' in navigator) {
      const patterns = {
        light: 10,
        medium: 20,
        heavy: 30
      };
      navigator.vibrate(patterns[type] || patterns.light);
    }
  }

  // Service worker message handler
  handleServiceWorkerMessage(data) {
    console.log('[MobileApp] Service worker message:', data);

    if (data.type === 'MESSAGE_SYNCED') {
      this.showNotification('Message sent successfully');
      this.loadConversationHistory();
    }
  }

  showNotification(message) {
    // Simple toast notification
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      bottom: 80px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 12px 24px;
      border-radius: 24px;
      z-index: 10000;
      font-size: 14px;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 3000);
  }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.app = new MobileApp();
  });
} else {
  window.app = new MobileApp();
}
