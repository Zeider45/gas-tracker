import { Router } from "express";
import { authMiddleware } from "../auth";
import {
  getActiveTrip,
  startTrip,
  addPoint,
  stopTrip,
  listTripPoints,
  getAllTrips,
  convertTripsToCSV,
} from "../trips";
import { z } from "zod";

const router = Router();

router.use(authMiddleware);

router.get("/active", async (req, res) => {
  try {
    const trip = await getActiveTrip(req.user!.id);
    if (!trip) return res.json({ active: null });
    const points = await listTripPoints(trip.id, 50);
    return res.json({ active: trip, points });
  } catch (e) {
    return res.status(500).json({ error: "db_error" });
  }
});

router.post("/start", async (req, res) => {
  const schema = z.object({
    initialFuelLiters: z.number().positive().optional(),
  });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success)
    return res
      .status(400)
      .json({ error: "validation", details: parsed.error.issues });
  try {
    const existing = await getActiveTrip(req.user!.id);
    if (existing) return res.status(409).json({ error: "trip_active" });
    const trip = await startTrip(req.user!.id, parsed.data.initialFuelLiters);
    return res.status(201).json({ trip });
  } catch (e) {
    return res.status(500).json({ error: "db_error" });
  }
});

router.post("/point", async (req, res) => {
  const schema = z.object({
    lat: z.number().min(-90).max(90),
    lng: z.number().min(-180).max(180),
  });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success)
    return res
      .status(400)
      .json({ error: "validation", details: parsed.error.issues });
  try {
    const trip = await getActiveTrip(req.user!.id);
    if (!trip) return res.status(404).json({ error: "no_active_trip" });
    const result = await addPoint(trip.id, parsed.data.lat, parsed.data.lng);
    return res.json(result);
  } catch (e) {
    return res.status(500).json({ error: "db_error" });
  }
});

router.post("/stop", async (req, res) => {
  const schema = z.object({
    finalFuelLiters: z.number().positive().optional(),
  });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success)
    return res
      .status(400)
      .json({ error: "validation", details: parsed.error.issues });
  try {
    const trip = await getActiveTrip(req.user!.id);
    if (!trip) return res.status(404).json({ error: "no_active_trip" });
    const updated = await stopTrip(trip.id, parsed.data.finalFuelLiters);
    return res.json({ trip: updated });
  } catch (e) {
    return res.status(500).json({ error: "db_error" });
  }
});

router.get("/export/csv", async (req, res) => {
  try {
    const trips = await getAllTrips(req.user!.id);
    const csv = convertTripsToCSV(trips);
    res.setHeader("Content-Type", "text/csv");
    res.setHeader("Content-Disposition", "attachment; filename=trips.csv");
    return res.send(csv);
  } catch (e) {
    return res.status(500).json({ error: "db_error" });
  }
});

export default router;
