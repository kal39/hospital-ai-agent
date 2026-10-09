import { NextFunction, Request, Response } from "express";
import { AuthenticatedPatient } from "../types/chat.js";
declare global {
    namespace Express {
        interface Request {
            patient?: AuthenticatedPatient;
        }
    }
}
export declare function authenticatePatient(req: Request, res: Response, next: NextFunction): void;
//# sourceMappingURL=auth.middleware.d.ts.map