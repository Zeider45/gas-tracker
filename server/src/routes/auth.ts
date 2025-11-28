import { Router } from "express";
import { db } from "../db";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { signToken, authMiddleware } from "../auth";

const router = Router();

const credsSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

router.post("/signup", (req, res) => {
  const parsed = credsSchema.safeParse(req.body);
  if (!parsed.success)
    return res
      .status(400)
      .json({ error: "validation", details: parsed.error.issues });
  const { email, password } = parsed.data;
  const password_hash = bcrypt.hashSync(password, 10);
  const stmt = db.prepare(
    "INSERT INTO users (email, password_hash) VALUES (?, ?)"
  );
  stmt.run(email, password_hash, function (this: any, err: Error | null) {
    if (err) {
      if (err.message.includes("UNIQUE"))
        return res.status(409).json({ error: "email_taken" });
      return res.status(500).json({ error: "db_error" });
    }
    const user = { id: Number(this.lastID), email };
    const token = signToken(user);
    return res.status(201).json({ token, user });
  });
});

router.post("/login", (req, res) => {
  const parsed = credsSchema.safeParse(req.body);
  if (!parsed.success)
    return res
      .status(400)
      .json({ error: "validation", details: parsed.error.issues });
  const { email, password } = parsed.data;
  db.get(
    "SELECT id, email, password_hash FROM users WHERE email = ?",
    [email],
    (err, row: any) => {
      if (err) return res.status(500).json({ error: "db_error" });
      if (!row) return res.status(401).json({ error: "invalid_credentials" });
      if (!bcrypt.compareSync(password, row.password_hash))
        return res.status(401).json({ error: "invalid_credentials" });
      const user = { id: row.id, email: row.email };
      const token = signToken(user);
      return res.json({ token, user });
    }
  );
});

router.get("/me", authMiddleware, (req, res) => {
  return res.json({ user: req.user });
});

export default router;
