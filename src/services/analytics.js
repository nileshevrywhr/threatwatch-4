// Analytics service - no-op stub
// Original analytics removed; this preserves the export interface

class Analytics {
  initializeUmami() {}
  _getUmamiClient() { return null; }
  _retryFlushQueue() {}
  _generateSessionId() { return null; }
  _getStoredDistinctId() { return null; }
  _storeDistinctId() {}
  _flushQueue() {}
  _sendEvent() {}
  track() {}
  identify() {}
  trackPageView() {}
  trackAuthEvent() {}
  trackQuickScanUI() {}
  trackPDFInteraction() {}
  trackFunnelStep() {}
  trackEngagement() {}
  trackFormInteraction() {}
  trackError() {}
  trackAPIError() {}
  trackSubscription() {}
  trackFeatureUsage() {}
  trackPerformance() {}
  _classifyPerformance() {}
  startSession() {}
  endSession() {}
  getSessionId() { return null; }
  getDistinctId() { return null; }
  flush() {}
  reset() {}
}

export const frontendAnalytics = new Analytics();

export function useAnalytics() {
  return {
    track: (...args) => frontendAnalytics.track(...args),
    identify: (...args) => frontendAnalytics.identify(...args),
    trackPageView: (...args) => frontendAnalytics.trackPageView(...args),
    trackAuthEvent: (...args) => frontendAnalytics.trackAuthEvent(...args),
    trackQuickScanUI: (...args) => frontendAnalytics.trackQuickScanUI(...args),
    trackPDFInteraction: (...args) => frontendAnalytics.trackPDFInteraction(...args),
    trackFunnelStep: (...args) => frontendAnalytics.trackFunnelStep(...args),
    trackEngagement: (...args) => frontendAnalytics.trackEngagement(...args),
    trackFormInteraction: (...args) => frontendAnalytics.trackFormInteraction(...args),
    trackError: (...args) => frontendAnalytics.trackError(...args),
    trackAPIError: (...args) => frontendAnalytics.trackAPIError(...args),
    trackSubscription: (...args) => frontendAnalytics.trackSubscription(...args),
    trackFeatureUsage: (...args) => frontendAnalytics.trackFeatureUsage(...args),
    trackPerformance: (...args) => frontendAnalytics.trackPerformance(...args),
  };
}

export default frontendAnalytics;
