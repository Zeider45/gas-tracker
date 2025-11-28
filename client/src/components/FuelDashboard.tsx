import React, { useEffect, useState } from "react";
import { fuelSnapshot } from "../api";
import { useApp } from "../store";
import Card from "./ui/Card";
import Button from "./ui/Button";

// Small helper to format numbers or show em-dash
function fmt(value: number | null | undefined, digits = 2, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}${suffix}`;
}

const FuelDashboard: React.FC = () => {
  const { stats, refreshStats } = useApp();
  const [input, setInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    (async () => {
      await refreshStats();
      setLoaded(true);
      setUpdatedAt(new Date());
    })();
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setSaving(true);
    try {
      const val = parseFloat(input);
      if (isNaN(val)) throw new Error("Valor inválido");
      await fuelSnapshot(val);
      setInput("");
      await refreshStats();
      setUpdatedAt(new Date());
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card
      title={
        <span style={{ display: "flex", alignItems: "center", gap: ".5rem" }}>
          Combustible
          {stats?.samples ? (
            <span className="badge" title="Snapshots registrados">
              {stats.samples} muestras
            </span>
          ) : (
            <span className="badge" style={{ background: "#555" }}>
              SIN DATOS
            </span>
          )}
        </span>
      }
    >
      {!loaded && (
        <div style={{ fontSize: ".8rem", color: "var(--color-text-dim)" }}>
          Cargando...
        </div>
      )}
      {loaded && !stats && (
        <div style={{ fontSize: ".8rem", color: "var(--color-text-dim)" }}>
          Inicia sesión para ver estadísticas.
        </div>
      )}
      {stats && (
        <ul className="stats-list" style={{ marginBottom: ".75rem" }}>
          <li>
            <span>Actual</span>
            <strong>{fmt(stats.currentFuelLiters, 1, " L")}</strong>
          </li>
          <li>
            <span>Consumo medio</span>
            <strong>{fmt(stats.avgLitersPer100Km, 2, " L/100km")}</strong>
          </li>
          <li>
            <span>Promedio km/día</span>
            <strong>{fmt(stats.avgKmPerDay, 1, " km")}</strong>
          </li>
          <li>
            <span>Rango estimado</span>
            <strong>{fmt(stats.projectedRangeKm, 1, " km")}</strong>
          </li>
          <li>
            <span>Días restantes</span>
            <strong>{fmt(stats.projectedDaysLeft, 1, " días")}</strong>
          </li>
        </ul>
      )}
      <form
        onSubmit={save}
        style={{ display: "flex", gap: ".5rem", flexWrap: "wrap" }}
      >
        <div style={{ flex: "1 1 160px" }}>
          <input
            placeholder="Litros actuales"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
        </div>
        <Button type="submit" loading={saving} style={{ minWidth: "120px" }}>
          Snapshot
        </Button>
      </form>
      {updatedAt && stats && (
        <div style={{ marginTop: ".5rem", fontSize: ".65rem", opacity: 0.6 }}>
          Actualizado {updatedAt.toLocaleTimeString()}
        </div>
      )}
      {err && <div className="error">{err}</div>}
    </Card>
  );
};

export default FuelDashboard;
