import React from "react";
import AuthForm from "./components/AuthForm";
import TripTracker from "./components/TripTracker";
import FuelDashboard from "./components/FuelDashboard";
import NavBar from "./components/NavBar";
import InstallPrompt from "./components/InstallPrompt";
import { useApp } from "./store";

const App: React.FC = () => {
  const { user } = useApp();
  return (
    <div className="container fade-in">
      <NavBar />
      {!user && <AuthForm />}
      {user && (
        <div
          className="grid"
          style={{ gridTemplateColumns: "repeat(auto-fit,minmax(300px,1fr))" }}
        >
          <TripTracker />
          <FuelDashboard />
        </div>
      )}
      <div className="footer">PWA experimental — datos locales y API</div>
      <InstallPrompt />
    </div>
  );
};

export default App;
