// Performance Monitor
// Real User Monitoring (RUM) for PWA

class PerformanceMonitor {
  constructor() {
    this.metrics = {};
    this.apiEndpoint = '/api/analytics/performance';

    this.init();
  }

  init() {
    console.log('[PerformanceMonitor] Initializing...');

    // Wait for page load
    if (document.readyState === 'complete') {
      this.collectMetrics();
    } else {
      window.addEventListener('load', () => this.collectMetrics());
    }

    // Monitor long tasks
    this.observeLongTasks();

    // Monitor layout shifts
    this.observeLayoutShifts();

    // Monitor largest contentful paint
    this.observeLCP();

    // Monitor first input delay
    this.observeFID();

    console.log('[PerformanceMonitor] Initialized');
  }

  collectMetrics() {
    try {
      // Navigation Timing
      const navTiming = performance.getEntriesByType('navigation')[0];

      if (navTiming) {
        this.metrics.navigationTiming = {
          dnsLookup: navTiming.domainLookupEnd - navTiming.domainLookupStart,
          tcpConnection: navTiming.connectEnd - navTiming.connectStart,
          tlsNegotiation: navTiming.secureConnectionStart > 0 ?
            navTiming.connectEnd - navTiming.secureConnectionStart : 0,
          requestTime: navTiming.responseStart - navTiming.requestStart,
          responseTime: navTiming.responseEnd - navTiming.responseStart,
          domProcessing: navTiming.domContentLoadedEventEnd - navTiming.domContentLoadedEventStart,
          loadComplete: navTiming.loadEventEnd - navTiming.loadEventStart,
          totalTime: navTiming.loadEventEnd - navTiming.fetchStart
        };
      }

      // Paint Timing
      const paintEntries = performance.getEntriesByType('paint');
      paintEntries.forEach(entry => {
        if (entry.name === 'first-paint') {
          this.metrics.firstPaint = entry.startTime;
        } else if (entry.name === 'first-contentful-paint') {
          this.metrics.firstContentfulPaint = entry.startTime;
        }
      });

      // Resource Timing
      const resources = performance.getEntriesByType('resource');
      this.metrics.resources = {
        total: resources.length,
        byType: this.groupResourcesByType(resources),
        totalSize: this.calculateTotalSize(resources),
        slowest: this.getSlowestResources(resources, 5)
      };

      // Memory (if available)
      if (performance.memory) {
        this.metrics.memory = {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
          usagePercent: (performance.memory.usedJSHeapSize /
                        performance.memory.jsHeapSizeLimit * 100).toFixed(2)
        };
      }

      // Connection Info (if available)
      if (navigator.connection) {
        this.metrics.connection = {
          effectiveType: navigator.connection.effectiveType,
          downlink: navigator.connection.downlink,
          rtt: navigator.connection.rtt,
          saveData: navigator.connection.saveData
        };
      }

      // Device Info
      this.metrics.device = {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        hardwareConcurrency: navigator.hardwareConcurrency,
        deviceMemory: navigator.deviceMemory,
        screenResolution: `${window.screen.width}x${window.screen.height}`,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        pixelRatio: window.devicePixelRatio
      };

      // Service Worker Status
      if ('serviceWorker' in navigator) {
        this.metrics.serviceWorker = {
          controlled: !!navigator.serviceWorker.controller,
          ready: navigator.serviceWorker.ready !== null
        };
      }

      console.log('[PerformanceMonitor] Metrics collected:', this.metrics);

      // Send metrics
      this.sendMetrics();

    } catch (error) {
      console.error('[PerformanceMonitor] Collection error:', error);
    }
  }

  observeLongTasks() {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            console.warn('[PerformanceMonitor] Long task detected:', {
              duration: entry.duration,
              startTime: entry.startTime
            });

            if (!this.metrics.longTasks) {
              this.metrics.longTasks = [];
            }

            this.metrics.longTasks.push({
              duration: entry.duration,
              startTime: entry.startTime
            });
          }
        });

        observer.observe({ entryTypes: ['longtask'] });
      } catch (e) {
        // Long task API not supported
        console.log('[PerformanceMonitor] Long task API not supported');
      }
    }
  }

  observeLayoutShifts() {
    if ('PerformanceObserver' in window) {
      try {
        let clsScore = 0;

        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsScore += entry.value;
            }
          }

          this.metrics.cumulativeLayoutShift = clsScore.toFixed(4);

          if (clsScore > 0.1) {
            console.warn('[PerformanceMonitor] High CLS detected:', clsScore);
          }
        });

        observer.observe({ entryTypes: ['layout-shift'] });
      } catch (e) {
        console.log('[PerformanceMonitor] Layout Shift API not supported');
      }
    }
  }

  observeLCP() {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];

          this.metrics.largestContentfulPaint = lastEntry.startTime;

          if (lastEntry.startTime > 2500) {
            console.warn('[PerformanceMonitor] Slow LCP:', lastEntry.startTime);
          }
        });

        observer.observe({ entryTypes: ['largest-contentful-paint'] });
      } catch (e) {
        console.log('[PerformanceMonitor] LCP API not supported');
      }
    }
  }

  observeFID() {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.metrics.firstInputDelay = entry.processingStart - entry.startTime;

            if (entry.processingStart - entry.startTime > 100) {
              console.warn('[PerformanceMonitor] Slow FID:', entry.processingStart - entry.startTime);
            }
          }
        });

        observer.observe({ entryTypes: ['first-input'] });
      } catch (e) {
        console.log('[PerformanceMonitor] FID API not supported');
      }
    }
  }

  groupResourcesByType(resources) {
    const grouped = {};

    resources.forEach(resource => {
      const type = resource.initiatorType || 'other';

      if (!grouped[type]) {
        grouped[type] = {
          count: 0,
          totalDuration: 0
        };
      }

      grouped[type].count++;
      grouped[type].totalDuration += resource.duration;
    });

    return grouped;
  }

  calculateTotalSize(resources) {
    let total = 0;

    resources.forEach(resource => {
      if (resource.transferSize) {
        total += resource.transferSize;
      }
    });

    return {
      bytes: total,
      kb: (total / 1024).toFixed(2),
      mb: (total / 1024 / 1024).toFixed(2)
    };
  }

  getSlowestResources(resources, count = 5) {
    return resources
      .sort((a, b) => b.duration - a.duration)
      .slice(0, count)
      .map(resource => ({
        name: resource.name,
        duration: resource.duration,
        size: resource.transferSize,
        type: resource.initiatorType
      }));
  }

  async sendMetrics() {
    try {
      // Add session info
      const sessionData = {
        sessionId: this.getSessionId(),
        timestamp: Date.now(),
        url: window.location.href,
        referrer: document.referrer,
        userId: localStorage.getItem('userId'),
        metrics: this.metrics
      };

      // Send to analytics endpoint
      await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(sessionData)
      });

      console.log('[PerformanceMonitor] Metrics sent');

    } catch (error) {
      console.error('[PerformanceMonitor] Send error:', error);
    }
  }

  getSessionId() {
    let sessionId = sessionStorage.getItem('sessionId');

    if (!sessionId) {
      sessionId = 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
      sessionStorage.setItem('sessionId', sessionId);
    }

    return sessionId;
  }

  // Public API
  mark(name) {
    performance.mark(name);
  }

  measure(name, startMark, endMark) {
    try {
      performance.measure(name, startMark, endMark);
      const measure = performance.getEntriesByName(name)[0];

      console.log(`[PerformanceMonitor] ${name}: ${measure.duration.toFixed(2)}ms`);

      return measure.duration;
    } catch (error) {
      console.error('[PerformanceMonitor] Measure error:', error);
      return null;
    }
  }

  clearMarks() {
    performance.clearMarks();
    performance.clearMeasures();
  }

  getReport() {
    return {
      ...this.metrics,
      timestamp: Date.now(),
      url: window.location.href
    };
  }

  logReport() {
    console.table(this.metrics.navigationTiming);

    if (this.metrics.resources) {
      console.log('Resources:', this.metrics.resources);
    }

    if (this.metrics.memory) {
      console.log('Memory:', this.metrics.memory);
    }

    console.log('Core Web Vitals:');
    console.log('- LCP:', this.metrics.largestContentfulPaint?.toFixed(2) || 'N/A', 'ms');
    console.log('- FID:', this.metrics.firstInputDelay?.toFixed(2) || 'N/A', 'ms');
    console.log('- CLS:', this.metrics.cumulativeLayoutShift || 'N/A');
  }
}

// Initialize performance monitor
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.performanceMonitor = new PerformanceMonitor();
  });
} else {
  window.performanceMonitor = new PerformanceMonitor();
}

// Export for manual use
window.PerformanceMonitor = PerformanceMonitor;
