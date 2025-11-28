import express, { Request, Response } from "express";
import cors from "cors";
import dotenv from "dotenv";
import { initDatabase } from "./db";
import authRouter from "./routes/auth";
import tripsRouter from "./routes/trips";
import fuelRouter from "./routes/fuel";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

app.get("/health", (_req: Request, res: Response) => {
  res.json({ status: "ok", timestamp: Date.now() });
});

app.use("/auth", authRouter);
app.use("/trips", tripsRouter);
app.use("/fuel", fuelRouter);

const PORT = Number(process.env.PORT) || 4000;
const HOST = process.env.HOST || "0.0.0.0"; // listen on all interfaces for mobile access
initDatabase()
  .then(() => {
    app.listen(PORT, HOST, () => {
      console.log(`Gas Tracker API running on http://${HOST}:${PORT}`);
    });
  })
  .catch((err) => {
    console.error("Database init failed", err);
    process.exit(1);
  });
