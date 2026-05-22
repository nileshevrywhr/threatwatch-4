/* eslint-disable no-restricted-globals */
/**
 * Umami Analytics Service for ThreatWatch Frontend
 * Handles user journey tracking, drop-off analysis, and business metrics
 */

class ThreatWatchFrontendAnalytics {
  constructor() {
    this.isInitialized = false;
    this.eventQueue = [];
    this.maxQueueSize = 100;
    this.sessionId = this._generateSessionId();
    this.distinctId = this._getStoredDistinctId();
    this.initializeUmami();
  }

  initializeUmami() {
    try {
      if (typeof window === "undefined") {
        return;
      }

      this.isInitialized = true;

      if (this._getUmamiClient()) {
        this._flushQueue();
      } else {
        this._retryFlushQueue();
      }

      if (process.env.NODE_ENV === "development") {
        console.log("Umami frontend analytics initialized successfully");
      }
    } catch (error) {
      console.error("Failed to initialize Umami analytics:", error);
      this.isInitialized = false;
    }
  }

  _getUmamiClient() {
    if (typeof window === "undefined") {
      return null;
    }

    const { umami } = window;
    if (!umami) {
      return null;
    }

    if (typeof umami === "function") {
      return {
        track: (eventName, properties) => umami(eventName, properties),
      };
    }

    if (typeof umami.track === "function") {
      return {
        track: (eventName, properties) => umami.track(eventName, properties),
      };
    }

    return null;
  }

  _retryFlushQueue() {
    let attempts = 0;
    const maxAttempts = 20;

    const timer = setInterval(() => {
      attempts += 1;
      const client = this._getUmamiClient();

      if (client) {
        this._flushQueue();
        clearInterval(timer);
      } else if (attempts >= maxAttempts) {
        clearInterval(timer);
      }
    }, 500);
  }

  _generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  }

  _getStoredDistinctId() {
    if (typeof window === "undefined") {
      return null;
    }

    try {
      return window.localStorage.getItem("tw_umami_distinct_id");
    } catch (error) {
      return null;
    }
  }

  _storeDistinctId(userId) {
    if (typeof window === "undefined") {
      return;
    }

    try {
      if (userId) {
        window.localStorage.setItem("tw_umami_distinct_id", userId);
      } else {
        window.localStorage.removeItem("tw_umami_distinct_id");
      }
    } catch (error) {
      // Ignore storage failures in privacy-restricted environments.
    }
  }

  _flushQueue() {
    if (!this.eventQueue.length) {
      return;
    }

    const queuedEvents = [...this.eventQueue];
    this.eventQueue = [];
    queuedEvents.forEach(({ eventName, properties }) => {
      this._sendEvent(eventName, properties);
    });
  }

  _sendEvent(eventName, properties) {
    const client = this._getUmamiClient();
    if (!client) {
      return false;
    }

    client.track(eventName, properties);
    return true;
  }

  /**
   * Track events with standardized properties
   */
  track(eventName, properties = {}) {
    if (!this.isInitialized) return;

    try {
      const standardProperties = {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        pathname: window.location.pathname,
        user_agent: navigator.userAgent,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        viewport_size: `${window.innerWidth}x${window.innerHeight}`,
        tracking_source: "frontend",
      };

      const payload = { ...standardProperties, ...properties };
      const wasSent = this._sendEvent(eventName, payload);

      if (!wasSent) {
        this.eventQueue.push({ eventName, properties: payload });
        if (this.eventQueue.length > this.maxQueueSize) {
          this.eventQueue.shift();
        }
      }
    } catch (error) {
      if (process.env.NODE_ENV === "development") {
        console.error(`Failed to track event '${eventName}':`, error);
      }
    }
  }

  /**
   * Identify user for analytics
   */
  identify(userId, userProperties = {}) {
    if (!this.isInitialized) return;

    try {
      this.distinctId = userId;
      this._storeDistinctId(userId);
      this.track("identify", {
        user_id: userId,
        ...userProperties,
      });
    } catch (error) {
      if (process.env.NODE_ENV === "development") {
        console.error("Failed to identify user:", error);
      }
    }
  }

  // ============ USER JOURNEY TRACKING ============

  /**
   * Track page views manually
   */
  trackPageView(pageName, additionalProperties = {}) {
    this.track("page_view", {
      page_name: pageName,
      page_title: document.title,
      ...additionalProperties,
    });
  }

  /**
   * Track authentication events
   */
  trackAuthEvent(eventType, success = true, errorMessage = null) {
    this.track(`auth_${eventType}`, {
      success,
      error_message: errorMessage,
      auth_method: "email_password",
    });
  }

  /**
   * Track Quick Scan UI events - Key Metric #2: Search behavior
   */
  trackQuickScanUI(action, queryData = {}) {
    const properties = {
      action, // 'initiated', 'form_filled', 'submitted', 'results_viewed'
      query_length: queryData.query?.length || 0,
      has_query: Boolean(queryData.query),
      ...queryData,
    };

    this.track("quick_scan_ui", properties);
  }

  /**
   * Track PDF interaction events - Key Metric #3: Report engagement
   */
  trackPDFInteraction(action, reportData = {}) {
    const properties = {
      action, // 'generate_clicked', 'download_initiated', 'download_completed', 'download_failed'
      query: reportData.query || "unknown",
      ...reportData,
    };

    this.track("pdf_interaction", properties);
  }

  // ============ DROP-OFF ANALYSIS - Key Metric #4 ============

  /**
   * Track funnel steps for drop-off analysis
   */
  trackFunnelStep(funnelName, step, completed = true, timeOnStep = 0) {
    this.track(`funnel_${funnelName}_${step}`, {
      funnel_name: funnelName,
      step,
      completed,
      time_on_step_seconds: timeOnStep,
      step_timestamp: new Date().toISOString(),
    });
  }

  /**
   * Track user engagement metrics
   */
  trackEngagement(action, duration = 0, elementData = {}) {
    this.track("user_engagement", {
      action, // 'scroll', 'click', 'hover', 'focus', 'time_spent'
      duration_seconds: duration,
      element_type: elementData.type || "unknown",
      element_id: elementData.id || null,
      element_text: elementData.text || null,
      ...elementData,
    });
  }

  /**
   * Track form interactions for conversion analysis
   */
  trackFormInteraction(
    formName,
    action,
    fieldName = null,
    errorMessage = null,
  ) {
    this.track("form_interaction", {
      form_name: formName,
      action, // 'started', 'field_focused', 'field_completed', 'submitted', 'abandoned', 'error'
      field_name: fieldName,
      error_message: errorMessage,
      form_completion_time: Date.now(), // Can be used to calculate time to complete
    });
  }

  // ============ ERROR TRACKING ============

  /**
   * Track frontend errors
   */
  trackError(errorType, errorMessage, context = {}) {
    this.track("frontend_error", {
      error_type: errorType,
      error_message: errorMessage.substring(0, 500), // Truncate long messages
      stack_trace: context.stack || "",
      component: context.component || "unknown",
      severity: context.severity || "error",
      user_action: context.userAction || "unknown",
    });
  }

  /**
   * Track API errors from frontend
   */
  trackAPIError(endpoint, statusCode, errorMessage, requestData = {}) {
    this.track("api_error_frontend", {
      endpoint,
      status_code: statusCode,
      error_message: errorMessage,
      request_method: requestData.method || "GET",
      request_duration: requestData.duration || 0,
    });
  }

  // ============ BUSINESS METRICS ============

  /**
   * Track subscription-related events - Key Metric #5: Revenue
   */
  trackSubscription(action, planData = {}) {
    this.track("subscription_frontend", {
      action, // 'viewed_pricing', 'clicked_upgrade', 'payment_initiated', 'payment_completed', 'payment_failed'
      from_plan: planData.fromPlan || "free",
      to_plan: planData.toPlan || "unknown",
      pricing_page_time: planData.timeOnPage || 0,
    });
  }

  /**
   * Track feature discovery and adoption
   */
  trackFeatureUsage(featureName, action, metadata = {}) {
    this.track("feature_usage", {
      feature_name: featureName,
      action, // 'discovered', 'first_use', 'regular_use', 'abandoned'
      usage_context: metadata.context || "unknown",
      user_plan: metadata.userPlan || "free",
    });
  }

  // ============ PERFORMANCE TRACKING ============

  /**
   * Track performance metrics
   */
  trackPerformance(metricType, value, context = {}) {
    this.track("frontend_performance", {
      metric_type: metricType, // 'page_load', 'api_response', 'render_time', 'interaction_delay'
      value_ms: value,
      context,
      performance_tier: this._classifyPerformance(value),
    });
  }

  /**
   * Classify performance based on timing
   */
  _classifyPerformance(timeMs) {
    if (timeMs < 100) return "excellent";
    if (timeMs < 300) return "good";
    if (timeMs < 1000) return "acceptable";
    return "slow";
  }

  // ============ SESSION MANAGEMENT ============

  /**
   * Start session tracking
   */
  startSession(userInfo = {}) {
    this.track("session_started", {
      user_plan: userInfo.plan || "free",
      user_tier: userInfo.tier || "free",
      session_start_url: window.location.href,
    });
  }

  /**
   * End session tracking
   */
  endSession(sessionData = {}) {
    this.track("session_ended", {
      session_duration: sessionData.duration || 0,
      pages_visited: sessionData.pagesVisited || 1,
      actions_taken: sessionData.actionsTaken || 0,
      session_end_url: window.location.href,
    });
  }

  // ============ UTILITY METHODS ============

  /**
   * Get session ID for correlation
   */
  getSessionId() {
    return this.isInitialized ? this.sessionId : null;
  }

  /**
   * Get distinct ID for correlation
   */
  getDistinctId() {
    return this.isInitialized ? this.distinctId : null;
  }

  /**
   * Manually flush events
   */
  flush() {
    if (this.isInitialized) {
      this._flushQueue();
    }
  }

  /**
   * Reset analytics (for logout)
   */
  reset() {
    if (this.isInitialized) {
      this.distinctId = null;
      this._storeDistinctId(null);
      this.track("analytics_reset");
    }
  }
}

// Global analytics instance
export const frontendAnalytics = new ThreatWatchFrontendAnalytics();

// React hook for easy access
export const useAnalytics = () => {
  return frontendAnalytics;
};
