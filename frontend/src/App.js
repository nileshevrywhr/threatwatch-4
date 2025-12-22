import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { PostHogProvider } from "./components/PostHogProvider";
import LandingPage from "./components/LandingPage";
import IntelligenceFeed from "./components/IntelligenceFeed";
import PaymentSuccess from "./components/PaymentSuccess";
import { TooltipProvider } from "./components/ui/tooltip";

function App() {
  return (
    <PostHogProvider>
      <TooltipProvider>
        <div className="App">
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/feed" element={<IntelligenceFeed />} />
              <Route path="/payment-success" element={<PaymentSuccess />} />
            </Routes>
          </BrowserRouter>
        </div>
      </TooltipProvider>
    </PostHogProvider>
  );
}

export default App;