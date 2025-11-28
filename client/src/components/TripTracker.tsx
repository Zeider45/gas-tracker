import React, { useEffect, useRef, useState } from "react";
import { addPoint, startTrip, stopTrip } from "../api";
import { useApp } from "../store";
import Card from "./ui/Card";
import Button from "./ui/Button";

const TripTracker: React.FC = () => {
  const { trip, refreshTrip } = useApp();
  const [watching, setWatching] = useState(false);
  const intervalRef = useRef<number | null>(null);
  const [lastStatus, setLastStatus] = useState<string>("");

  async function begin() {
    await startTrip();
    await refreshTrip();
  }
  async function end() {
    await stopTrip();
    await refreshTrip();
    stopWatching();
  }

  function stopWatching() {
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setWatching(false);
  }

  async function tick() {
    if (!navigator.geolocation || !trip) return;
    navigator.geolocation.getCurrentPosition(async (pos) => {
      try {
        const { latitude, longitude } = pos.coords;
        const r = await addPoint(latitude, longitude);
        setLastStatus(
          `+${r.distanceAdded.toFixed(3)} km total ${r.total.toFixed(3)} km`
        );
        refreshTrip();
      } catch (e: any) {
        setLastStatus("Error enviando punto");
      }
    });
  }

  function startWatching() {
    if (watching) return;
    setWatching(true);
    tick();
    intervalRef.current = window.setInterval(tick, 5000);
  }

  useEffect(() => {
    refreshTrip();
  }, []);

  const maxDemoDistance = 500; // referencia para barra de progreso
  const pct = trip
    ? Math.min(100, (trip.total_distance_km / maxDemoDistance) * 100)
    : 0;
  return (
    <Card
      title={
        <span
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
          }}
        >
          Tracker de Viaje {trip && <span className="badge">Activo</span>}
        </span>
      }
    >
      {!trip && <Button onClick={begin}>Iniciar viaje</Button>}
      {trip && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: ".5rem",
            marginBottom: ".5rem",
          }}
        >
          {!watching && (
            <Button onClick={startWatching}>Comenzar seguimiento</Button>
          )}
          {watching && (
            <Button variant="secondary" onClick={stopWatching}>
              Pausar
            </Button>
          )}
          <Button variant="secondary" onClick={end}>
            Finalizar
          </Button>
        </div>
      )}
      {trip && (
        <div>
          <div style={{ fontSize: ".85rem", color: "var(--color-text-dim)" }}>
            Distancia total
          </div>
          <div style={{ fontSize: "1.4rem", fontWeight: 600 }}>
            {trip.total_distance_km.toFixed(2)} km
          </div>
          <div className="distance-bar">
            <span style={{ width: `${pct}%` }} />
          </div>
        </div>
      )}
      <p
        style={{
          minHeight: "1.2rem",
          fontSize: ".75rem",
          color: "var(--color-text-dim)",
          marginTop: ".6rem",
        }}
      >
        {lastStatus}
      </p>
    </Card>
  );
};

export default TripTracker;
