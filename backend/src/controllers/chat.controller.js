import { Request, Response } from "express";
import { randomUUID } from "crypto";
import { agentService } from "../services/agent.service";
import { ChatRequest } from "../types/chat";
export async function chatController(req, res) {
    try {
        const body = req.body;
        if (!req.patient) {
            res.status(401).json({
                error: "Patient authentication required.",
            });
            return;
        }
        const conversationId = body.conversationId ?? randomUUID();
        const language = body.language ?? "en";
        const result = await agentService.run(body.message, {
            patientId: req.patient.patientId,
            conversationId,
        }, language);
        res.json({
            conversationId,
            message: result.message,
            language,
            toolsUsed: result.toolsUsed,
            safetyFlag: result.safetyFlag,
        });
    }
    catch (error) {
        console.error(error);
        res.status(500).json({
            error: "The AI assistant could not process your request.",
        });
    }
}
//# sourceMappingURL=chat.controller.js.map