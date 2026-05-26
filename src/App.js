import React, { Suspense, lazy } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { AnalyticsProvider } from "./components/AnalyticsProvider";
import { Analytics } from "@vercel/analytics/react";
import { AuthProvider } from "./components/AuthProvider";
import { ThemeProvider } from "./components/ThemeProvider";
import LandingPage from "./components/LandingPage";
import ProtectedRoute from "./components/ProtectedRoute";
import ErrorBoundary from "./components/ErrorBoundary";
import { TooltipProvider } from "./components/ui/tooltip";

// Lazy load route components for performance optimization
const IntelligenceFeed = lazy(() => import("./components/IntelligenceFeed"));
const LoginPage = lazy(() => import("./components/LoginPage"));
const BillingSuccess = lazy(() => import("./components/BillingSuccess"));
const BillingCancel = lazy(() => import("./components/BillingCancel"));
const AuthCallback = lazy(() => import("./components/AuthCallback"));

const LoadingFallback = () => (
  <div className="min-h-screen bg-background flex flex-col items-center justify-center" role="status" aria-label="Loading application">
    <Loader2 className="h-10 w-10 animate-spin text-[#00FFB2]" />
    <p className="mt-4 text-muted-foreground animate-pulse font-medium">Loading...</p>
  </div>
);

function App() {
  return (
    <AnalyticsProvider>
      <AuthProvider>
        <ThemeProvider defaultTheme="system" storageKey="ui-theme">
          <TooltipProvider>
            <div className="App">
              <BrowserRouter>
                <ErrorBoundary>
                  <Suspense fallback={<LoadingFallback />}>
                    <Routes>
                      <Route path="/" element={<LandingPage />} />
                      <Route path="/login" element={<LoginPage />} />
                      <Route
                        path="/feed"
                        element={
                          <ProtectedRoute>
                            <IntelligenceFeed />
                          </ProtectedRoute>
                        }
                      />
                      <Route path="/billing/success" element={<BillingSuccess />} />
                      <Route path="/billing/cancel" element={<BillingCancel />} />
                      <Route path="/auth/callback" element={<AuthCallback />} />
                    </Routes>
                  </Suspense>
                </ErrorBoundary>
              </BrowserRouter>
              <Analytics />
            </div>
          </TooltipProvider>
        </ThemeProvider>
      </AuthProvider>
    </AnalyticsProvider>
  );
}

export default App;
