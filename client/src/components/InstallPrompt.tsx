import React, { useEffect, useState } from "react";
import Card from "./ui/Card";
import Button from "./ui/Button";

// Component to show PWA install banner when beforeinstallprompt fires
const InstallPrompt: React.FC = () => {
  const [deferredEvt, setDeferredEvt] = useState<any>(null);
  const [installed, setInstalled] = useState(false);

  useEffect(() => {
    function handleBeforeInstall(e: any) {
      e.preventDefault(); // prevent mini-infobar
      setDeferredEvt(e);
    }
    function handleInstalled() {
      setInstalled(true);
      setDeferredEvt(null);
    }
    window.addEventListener("beforeinstallprompt", handleBeforeInstall);
    window.addEventListener("appinstalled", handleInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
      window.removeEventListener("appinstalled", handleInstalled);
    };
  }, []);

  if (installed || !deferredEvt) return null;

  async function install() {
    if (!deferredEvt) return;
    deferredEvt.prompt();
    const choice = await deferredEvt.userChoice;
    if (choice.outcome === "accepted") {
      setInstalled(true);
    }
    setDeferredEvt(null);
  }

  return (
    <div
      style={{
        position: "fixed",
        bottom: "1rem",
        left: "1rem",
        maxWidth: 300,
        zIndex: 50,
      }}
    >
      <Card
        title={
          <span style={{ display: "flex", alignItems: "center", gap: ".4rem" }}>
            📱 Instalar App
          </span>
        }
      >
        <p style={{ fontSize: ".75rem", margin: "0 0 .5rem" }}>
          Instala la PWA para usarla como aplicación independiente.
        </p>
        <div style={{ display: "flex", gap: ".5rem" }}>
          <Button onClick={install}>Instalar</Button>
          <Button variant="secondary" onClick={() => setDeferredEvt(null)}>
            Cerrar
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default InstallPrompt;
