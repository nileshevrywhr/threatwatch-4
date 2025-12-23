import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { PostHogProvider } from "./components/PostHogProvider";
import { AuthProvider } from "./components/AuthProvider";
import LandingPage from "./components/LandingPage";
import IntelligenceFeed from "./components/IntelligenceFeed";
import PaymentSuccess from "./components/PaymentSuccess";
import LoginPage from "./components/LoginPage";
import ProtectedRoute from "./components/ProtectedRoute";
import { TooltipProvider } from "./components/ui/tooltip";

/**
 * Root application component that composes global providers and client-side routes.
 *
 * Provides PostHog, authentication, and tooltip contexts and defines the app routes:
 * "/" (LandingPage), "/login" (LoginPage), "/feed" (protected IntelligenceFeed), and "/payment-success" (PaymentSuccess).
 *
 * @returns {JSX.Element} The top-level JSX element for the application with global providers and configured routes.
 */
function App() {
  return (
    <PostHogProvider>
      <AuthProvider>
        <TooltipProvider>
          <div className="App">
            <BrowserRouter>
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
              </Routes>
            </BrowserRouter>
          </div>
        </TooltipProvider>
      </AuthProvider>
    </PostHogProvider>
  );
}

export default App;