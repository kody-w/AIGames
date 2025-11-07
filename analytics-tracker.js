/**
 * AI Ambassador Platform Analytics Tracker
 *
 * Lightweight JavaScript library for tracking user interactions and events.
 *
 * Usage:
 * 1. Include this script in your HTML:
 *    <script src="analytics-tracker.js"></script>
 *
 * 2. Initialize with your API endpoint:
 *    AnalyticsTracker.init('http://localhost:7071/api');
 *
 * 3. Track events:
 *    AnalyticsTracker.track('page_view', { page: 'home' });
 *    AnalyticsTracker.trackQRScan('ambassador-123');
 *    AnalyticsTracker.trackMessage('ambassador-123');
 */

(function(window) {
    'use strict';

    const AnalyticsTracker = {
        apiBaseUrl: null,
        userId: null,
        sessionId: null,
        ambassadorId: null,
        autoTrack: true,
        debugMode: false,

        /**
         * Initialize the analytics tracker
         * @param {string} apiBaseUrl - Base URL for analytics API
         * @param {object} options - Configuration options
         */
        init: function(apiBaseUrl, options = {}) {
            this.apiBaseUrl = apiBaseUrl;
            this.autoTrack = options.autoTrack !== false;
            this.debugMode = options.debugMode || false;
            this.ambassadorId = options.ambassadorId || null;

            // Get or create user ID
            this.userId = this._getUserId();

            // Get or create session ID
            this.sessionId = this._getSessionId();

            // Auto-track page view
            if (this.autoTrack) {
                this._setupAutoTracking();
            }

            this._log('Analytics Tracker initialized', {
                userId: this.userId,
                sessionId: this.sessionId,
                ambassadorId: this.ambassadorId
            });
        },

        /**
         * Track a custom event
         * @param {string} eventType - Type of event
         * @param {object} properties - Event properties
         */
        track: function(eventType, properties = {}) {
            const event = {
                event_type: eventType,
                user_id: this.userId,
                session_id: this.sessionId,
                ambassador_id: this.ambassadorId,
                properties: {
                    ...properties,
                    url: window.location.href,
                    referrer: document.referrer,
                    timestamp: new Date().toISOString()
                }
            };

            this._sendEvent(event);
        },

        /**
         * Track page view
         * @param {object} properties - Additional properties
         */
        trackPageView: function(properties = {}) {
            this.track('page_view', {
                page_title: document.title,
                page_path: window.location.pathname,
                ...properties
            });
        },

        /**
         * Track QR code scan
         * @param {string} ambassadorId - Ambassador ID
         * @param {object} properties - Additional properties
         */
        trackQRScan: function(ambassadorId, properties = {}) {
            this.ambassadorId = ambassadorId;
            this.track('qr_scan', {
                ambassador_id: ambassadorId,
                source: properties.source || 'direct',
                ...properties
            });
        },

        /**
         * Track ambassador entry
         * @param {string} ambassadorId - Ambassador ID
         * @param {object} properties - Additional properties
         */
        trackAmbassadorEntry: function(ambassadorId, properties = {}) {
            this.ambassadorId = ambassadorId;
            this.track('ambassador_entry', {
                ambassador_id: ambassadorId,
                ...properties
            });
        },

        /**
         * Track message sent
         * @param {object} properties - Additional properties
         */
        trackMessage: function(properties = {}) {
            this.track('message_sent', {
                message_length: properties.message_length || 0,
                ...properties
            });
        },

        /**
         * Track gallery view
         * @param {object} properties - Additional properties
         */
        trackGalleryView: function(properties = {}) {
            this.track('gallery_view', properties);
        },

        /**
         * Track share action
         * @param {string} ambassadorId - Ambassador ID
         * @param {string} method - Share method (link, social, etc.)
         */
        trackShare: function(ambassadorId, method = 'link') {
            this.track('share_ambassador', {
                ambassador_id: ambassadorId,
                share_method: method
            });
        },

        /**
         * Track bookmark action
         * @param {string} ambassadorId - Ambassador ID
         */
        trackBookmark: function(ambassadorId) {
            this.track('bookmark_ambassador', {
                ambassador_id: ambassadorId
            });
        },

        /**
         * Start a new session
         */
        startSession: function() {
            this.sessionId = this._generateId();
            this._setSessionId(this.sessionId);
            this.track('session_start', {});
        },

        /**
         * End current session
         */
        endSession: function() {
            this.track('session_end', {
                duration: this._getSessionDuration()
            });
        },

        /**
         * Set user ID
         * @param {string} userId - User ID
         */
        setUserId: function(userId) {
            this.userId = userId;
            localStorage.setItem('analytics_user_id', userId);
        },

        /**
         * Set ambassador ID
         * @param {string} ambassadorId - Ambassador ID
         */
        setAmbassadorId: function(ambassadorId) {
            this.ambassadorId = ambassadorId;
        },

        // Private methods

        /**
         * Get or create user ID
         * @private
         */
        _getUserId: function() {
            let userId = localStorage.getItem('analytics_user_id');
            if (!userId) {
                userId = this._generateId();
                localStorage.setItem('analytics_user_id', userId);
            }
            return userId;
        },

        /**
         * Get or create session ID
         * @private
         */
        _getSessionId: function() {
            let sessionId = sessionStorage.getItem('analytics_session_id');
            if (!sessionId) {
                sessionId = this._generateId();
                this._setSessionId(sessionId);
                sessionStorage.setItem('session_start_time', Date.now().toString());
            }
            return sessionId;
        },

        /**
         * Set session ID
         * @private
         */
        _setSessionId: function(sessionId) {
            sessionStorage.setItem('analytics_session_id', sessionId);
        },

        /**
         * Get session duration in seconds
         * @private
         */
        _getSessionDuration: function() {
            const startTime = parseInt(sessionStorage.getItem('session_start_time') || Date.now());
            return Math.floor((Date.now() - startTime) / 1000);
        },

        /**
         * Generate unique ID
         * @private
         */
        _generateId: function() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        },

        /**
         * Send event to analytics API
         * @private
         */
        _sendEvent: function(event) {
            if (!this.apiBaseUrl) {
                this._log('Analytics API not configured');
                return;
            }

            this._log('Tracking event:', event);

            // Send event via fetch API
            fetch(`${this.apiBaseUrl}/analytics/track`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(event),
                // Don't wait for response
                keepalive: true
            }).catch(error => {
                this._log('Error tracking event:', error);
            });
        },

        /**
         * Setup automatic tracking
         * @private
         */
        _setupAutoTracking: function() {
            // Track initial page view
            this.trackPageView();

            // Track clicks
            document.addEventListener('click', (e) => {
                const target = e.target;

                // Track button clicks
                if (target.tagName === 'BUTTON' || target.closest('button')) {
                    const button = target.tagName === 'BUTTON' ? target : target.closest('button');
                    this.track('button_click', {
                        button_text: button.textContent.trim(),
                        button_id: button.id
                    });
                }

                // Track link clicks
                if (target.tagName === 'A' || target.closest('a')) {
                    const link = target.tagName === 'A' ? target : target.closest('a');
                    this.track('link_click', {
                        link_text: link.textContent.trim(),
                        link_url: link.href
                    });
                }
            });

            // Track page visibility (session end on page hide)
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    this.endSession();
                }
            });

            // Track page unload
            window.addEventListener('beforeunload', () => {
                this.endSession();
            });

            // Track scroll depth
            let maxScrollDepth = 0;
            window.addEventListener('scroll', this._debounce(() => {
                const scrollDepth = Math.round(
                    (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
                );
                if (scrollDepth > maxScrollDepth) {
                    maxScrollDepth = scrollDepth;
                    if (scrollDepth >= 25 && scrollDepth < 50) {
                        this.track('scroll_depth', { depth: 25 });
                    } else if (scrollDepth >= 50 && scrollDepth < 75) {
                        this.track('scroll_depth', { depth: 50 });
                    } else if (scrollDepth >= 75 && scrollDepth < 100) {
                        this.track('scroll_depth', { depth: 75 });
                    } else if (scrollDepth >= 100) {
                        this.track('scroll_depth', { depth: 100 });
                    }
                }
            }, 1000));
        },

        /**
         * Debounce function
         * @private
         */
        _debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Log debug messages
         * @private
         */
        _log: function(...args) {
            if (this.debugMode) {
                console.log('[Analytics]', ...args);
            }
        }
    };

    // Export to global scope
    window.AnalyticsTracker = AnalyticsTracker;

})(window);


// Example usage documentation
/**
 * EXAMPLES:
 *
 * // Basic initialization
 * AnalyticsTracker.init('http://localhost:7071/api');
 *
 * // With options
 * AnalyticsTracker.init('http://localhost:7071/api', {
 *   autoTrack: true,
 *   debugMode: true,
 *   ambassadorId: 'creative-ambassador-001'
 * });
 *
 * // Track custom events
 * AnalyticsTracker.track('custom_event', {
 *   custom_property: 'value'
 * });
 *
 * // Track specific actions
 * AnalyticsTracker.trackQRScan('ambassador-123', { source: 'poster' });
 * AnalyticsTracker.trackMessage({ message_length: 50 });
 * AnalyticsTracker.trackShare('ambassador-123', 'facebook');
 * AnalyticsTracker.trackBookmark('ambassador-123');
 *
 * // Set identifiers
 * AnalyticsTracker.setUserId('user-guid-here');
 * AnalyticsTracker.setAmbassadorId('ambassador-123');
 */
