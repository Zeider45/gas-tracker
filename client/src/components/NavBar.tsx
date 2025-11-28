import React from "react";
import { useApp } from "../store";
import Button from "./ui/Button";

const NavBar: React.FC = () => {
  const { user, doLogout, toggleTheme, theme } = useApp();
  return (
    <nav className="nav">
      <div className="nav-title">⛽ Gas Tracker</div>
      <div className="nav-actions">
        {user && (
          <span className="badge" title={user.email}>
            {user.email}
          </span>
        )}
        <Button type="button" variant="secondary" onClick={toggleTheme}>
          {theme === "dark" ? "☀️ Claro" : "🌙 Oscuro"}
        </Button>
        {user && (
          <Button type="button" onClick={doLogout}>
            Salir
          </Button>
        )}
      </div>
    </nav>
  );
};

export default NavBar;
