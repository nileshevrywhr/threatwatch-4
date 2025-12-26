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
import ErrorBoundary from "./components/ErrorBoundary";
import { TooltipProvider } from "./components/ui/tooltip";

function App() {
  return (
    <PostHogProvider>
      <AuthProvider>
        <TooltipProvider>
          <div className="App">
            <BrowserRouter>
              <ErrorBoundary>
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
              </ErrorBoundary>
            </BrowserRouter>
          </div>
        </TooltipProvider>
      </AuthProvider>
    </PostHogProvider>
  );
}

export default App;
