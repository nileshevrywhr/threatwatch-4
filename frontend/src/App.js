import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./components/LandingPage";
import IntelligenceFeed from "./components/IntelligenceFeed";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/feed" element={<IntelligenceFeed />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;