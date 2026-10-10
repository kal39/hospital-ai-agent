
import { afterEach, describe, expect, it, vi } from "vitest";

const { generateWithToolsMock } = vi.hoisted(() => ({
  generateWithToolsMock: vi.fn(),
}));

vi.mock("./llm.service.js", () => ({
  llmService: {
    generateWithTools: generateWithToolsMock,
  },
}));

import { agentService } from "./agent.service.js";

describe("Agent conversation isolation", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("isolates conversation history between patients sharing a conversation ID", async () => {
    const conversationId = `isolation-test-${Date.now()}`;

    const capturedHistories: Array<
      Array<{ role: string; content: string }>
    > = [];

    generateWithToolsMock.mockImplementation(async (input) => {
      capturedHistories.push(
        input.conversationHistory.map(
          (message: { role: string; content: string }) => ({
            role: message.role,
            content: message.content,
          })
        )
      );

      return {
        message: "Test response.",
        toolsUsed: [],
      };
    });

    await agentService.run(
      "PATIENT_ONE_PRIVATE_MESSAGE",
      { patientId: "patient-001", conversationId },
      "en"
    );

    await agentService.run(
      "PATIENT_TWO_PRIVATE_MESSAGE",
      { patientId: "patient-002", conversationId },
      "en"
    );

    await agentService.run(
      "PATIENT_ONE_FOLLOW_UP",
      { patientId: "patient-001", conversationId },
      "en"
    );

    expect(capturedHistories).toHaveLength(3);

    // Neither patient's first request should contain prior history.
    expect(capturedHistories[0]).toEqual([]);
    expect(capturedHistories[1]).toEqual([]);

    // Patient 1's follow-up must contain Patient 1's earlier message.
    expect(capturedHistories[2]).toContainEqual(
      expect.objectContaining({
        role: "user",
        content: "PATIENT_ONE_PRIVATE_MESSAGE",
      })
    );

    // Patient 1's history must not contain Patient 2's private message.
    expect(capturedHistories[2]).not.toContainEqual(
      expect.objectContaining({
        role: "user",
        content: "PATIENT_TWO_PRIVATE_MESSAGE",
      })
    );
  });
});
