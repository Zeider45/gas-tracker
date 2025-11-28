import { Router } from "express";
import { authMiddleware } from "../auth";
import { z } from "zod";
import { computeConsumptionStats, recordFuelSnapshot } from "../calc";

const router = Router();
router.use(authMiddleware);

router.post("/snapshot", async (req, res) => {
  const schema = z.object({ fuelLiters: z.number().min(0).max(200) });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success)
    return res
      .status(400)
      .json({ error: "validation", details: parsed.error.issues });
  try {
    await recordFuelSnapshot(req.user!.id, parsed.data.fuelLiters);
    return res.status(201).json({ ok: true });
  } catch (e) {
    return res.status(500).json({ error: "db_error" });
  }
});

router.get("/stats", async (req, res) => {
  try {
    const stats = await computeConsumptionStats(req.user!.id);
    return res.json(stats);
  } catch (e) {
    return res.status(500).json({ error: "db_error" });
  }
});

export default router;
