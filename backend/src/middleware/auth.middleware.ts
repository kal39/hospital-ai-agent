
import { NextFunction, Request, Response } from "express";
import { env } from "../config/env.js";
import { AuthenticatedPatient } from "../types/chat.js";

declare global {
  namespace Express {
    interface Request {
      patient?: AuthenticatedPatient;
    }
  }
}

const SYNTHETIC_PATIENT_IDS = new Set([
  "patient-001",
  "patient-002",
]);

/**
 * DEMO AUTHENTICATION ONLY.
 *
 * This permits access only to predefined synthetic patients in
 * development when demo authentication is explicitly enabled.
 *
 * Production must verify the hospital portal's session or token
 * and derive patient identity from the verified authentication context.
 */
export function authenticatePatient(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  if (
    env.nodeEnv !== "development" ||
    !env.demoAuthEnabled
  ) {
    res.status(401).json({
      error: "Authentication is required.",
    });
    return;
  }

  const patientId = req.header("x-demo-patient-id");

  if (!patientId) {
    res.status(401).json({
      error: "Provide a synthetic demo patient identity.",
    });
    return;
  }

  if (!SYNTHETIC_PATIENT_IDS.has(patientId)) {
    res.status(403).json({
      error: "The requested demo patient is not permitted.",
    });
    return;
  }

  req.patient = { patientId };
  next();
}
