/**
 * PostHog Provider Component for ThreatWatch
 * Provides PostHog context throughout the React application
 */
import React, { createContext, useContext, useEffect, useState } from 'react'
import posthog from 'posthog-js'
import { frontendAnalytics } from '../services/analytics'

const PostHogContext = createContext()

export const PostHogProvider = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    // Initialize PostHog if not already done
    if (frontendAnalytics.isInitialized) {
      setIsInitialized(true)
    } else {
      // Wait a bit and check again in case initialization is in progress
      const timer = setTimeout(() => {
        setIsInitialized(frontendAnalytics.isInitialized)
      }, 100)

      return () => clearTimeout(timer)
    }
  }, [])

  useEffect(() => {
    // Track initial page view
    if (isInitialized) {
      frontendAnalytics.trackPageView('app_loaded', {
        initial_load: true,
        referrer: document.referrer || 'direct'
      })
    }
  }, [isInitialized])

  const contextValue = {
    posthog: isInitialized ? posthog : null,
    analytics: frontendAnalytics,
    isInitialized
  }

  return (
    <PostHogContext.Provider value={contextValue}>
      {children}
    </PostHogContext.Provider>
  )
}

export const usePostHog = () => {
  const context = useContext(PostHogContext)
  if (!context) {
    throw new Error('usePostHog must be used within PostHogProvider')
  }
  return context
}