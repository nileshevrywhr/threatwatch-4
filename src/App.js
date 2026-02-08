import React, { Suspense, lazy } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { PostHogProvider } from "./components/PostHogProvider";
import { AuthProvider } from "./components/AuthProvider";
import LandingPage from "./components/LandingPage";
import ProtectedRoute from "./components/ProtectedRoute";
import ErrorBoundary from "./components/ErrorBoundary";
import { TooltipProvider } from "./components/ui/tooltip";

// Lazy load route components for performance optimization
const IntelligenceFeed = lazy(() => import("./components/IntelligenceFeed"));
const LoginPage = lazy(() => import("./components/LoginPage"));
const PaymentSuccess = lazy(() => import("./components/PaymentSuccess"));
const AuthCallback = lazy(() => import("./components/AuthCallback"));

const LoadingFallback = () => (
  <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center" role="status" aria-label="Loading application">
    <Loader2 className="h-10 w-10 animate-spin text-cyan-500" />
    <p className="mt-4 text-slate-400 animate-pulse font-medium">Loading...</p>
  </div>
);

function App() {
  return (
    <PostHogProvider>
      <AuthProvider>
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
                    <Route path="/payment-success" element={<PaymentSuccess />} />
                    <Route path="/auth/callback" element={<AuthCallback />} />
                  </Routes>
                </Suspense>
              </ErrorBoundary>
            </BrowserRouter>
          </div>
        </TooltipProvider>
      </AuthProvider>
    </PostHogProvider>
  );
}

export default App;
