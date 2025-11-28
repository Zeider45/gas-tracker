import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";

export interface AuthUser {
  id: number;
  email: string;
}

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Express {
    interface Request {
      user?: AuthUser;
    }
  }
}

const JWT_SECRET = process.env.JWT_SECRET || "dev-secret";

export function signToken(user: AuthUser): string {
  return jwt.sign({ sub: user.id, email: user.email }, JWT_SECRET, {
    expiresIn: "7d",
  });
}

export function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const auth = req.headers.authorization;
  if (!auth) return res.status(401).json({ error: "missing_authorization" });
  const [scheme, token] = auth.split(" ");
  if (scheme !== "Bearer" || !token)
    return res.status(401).json({ error: "invalid_authorization" });
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    if (typeof decoded !== "object" || decoded === null) {
      return res.status(401).json({ error: "invalid_token" });
    }
    const maybe: any = decoded;
    if (maybe.sub === undefined || maybe.email === undefined) {
      return res.status(401).json({ error: "invalid_token" });
    }
    req.user = { id: Number(maybe.sub), email: String(maybe.email) };
    next();
  } catch (e) {
    return res.status(401).json({ error: "invalid_token" });
  }
}
