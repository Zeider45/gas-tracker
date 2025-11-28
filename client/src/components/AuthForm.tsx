import React, { useState } from "react";
import { signup, login } from "../api";
import { useApp } from "../store";
import Card from "./ui/Card";
import Button from "./ui/Button";

const AuthForm: React.FC = () => {
  const { setUser } = useApp();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [error, setError] = useState<string | null>(null);
  const [showPass, setShowPass] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const user =
        mode === "signup"
          ? await signup(email, password)
          : await login(email, password);
      setUser(user);
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <Card
      className="fade-in"
      style={{ maxWidth: 420, margin: "0 auto" }}
      title={mode === "signup" ? "Crear cuenta" : "Iniciar sesión"}
    >
      <form onSubmit={submit}>
        <label>
          Email
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
            placeholder="tu@email.com"
          />
        </label>
        <label>
          Contraseña
          <div style={{ position: "relative" }}>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type={showPass ? "text" : "password"}
              required
              minLength={6}
              placeholder="••••••"
            />
            <button
              type="button"
              className="btn-secondary"
              style={{
                position: "absolute",
                top: 4,
                right: 4,
                padding: "0.35rem .6rem",
              }}
              onClick={() => setShowPass((s) => !s)}
            >
              {showPass ? "Ocultar" : "Ver"}
            </button>
          </div>
        </label>
        {error && <div className="error">{error}</div>}
        <div style={{ display: "flex", gap: ".5rem", marginTop: "0.75rem" }}>
          <Button type="submit">
            {mode === "signup" ? "Registrarse" : "Entrar"}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setMode(mode === "signup" ? "login" : "signup")}
          >
            {mode === "signup" ? "Ya tengo cuenta" : "Crear cuenta"}
          </Button>
        </div>
      </form>
    </Card>
  );
};

export default AuthForm;
