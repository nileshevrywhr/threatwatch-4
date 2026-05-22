/**
 * Analytics Provider Component for ThreatWatch
 * Provides analytics context throughout the React application
 */
import React, { createContext, useContext, useEffect, useState } from 'react'
import { frontendAnalytics } from '../services/analytics'

const AnalyticsContext = createContext()

export const AnalyticsProvider = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    if (frontendAnalytics.isInitialized) {
      setIsInitialized(true)
    } else {
      const timer = setTimeout(() => {
        setIsInitialized(frontendAnalytics.isInitialized)
      }, 100)

      return () => clearTimeout(timer)
    }
  }, [])

  useEffect(() => {
    if (isInitialized) {
      frontendAnalytics.trackPageView('app_loaded', {
        initial_load: true,
        referrer: document.referrer || 'direct'
      })
    }
  }, [isInitialized])

  const contextValue = {
    analytics: frontendAnalytics,
    isInitialized
  }

  return (
    <AnalyticsContext.Provider value={contextValue}>
      {children}
    </AnalyticsContext.Provider>
  )
}

export const useAnalyticsContext = () => {
  const context = useContext(AnalyticsContext)
  if (!context) {
    throw new Error('useAnalyticsContext must be used within AnalyticsProvider')
  }
  return context
}
