import { NextFunction, Request, Response } from "express";
import { AuthenticatedPatient } from "../types/chat.js";

declare global {
  namespace Express {
    interface Request {
      patient?: AuthenticatedPatient;
    }
  }
}

export function authenticatePatient(
  req: Request,
  res: Response,
  next: NextFunction
) {
  /*
   * DEMO ONLY:
   * The real hospital portal should provide the authenticated
   * patient identity through its secure session/token.
   *
   * Never trust a patientId supplied in the request body.
   */

  const patientId =
    req.header("x-demo-patient-id") ?? "patient-001";

  req.patient = {
    patientId,
  };

  next();
}