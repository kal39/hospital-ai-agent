import "dotenv/config";
import { GoogleGenAI } from "@google/genai";

const apiKey = process.env.LLM_API_KEY;

if (!apiKey) {
  throw new Error("LLM_API_KEY is missing.");
}

const ai = new GoogleGenAI({
  apiKey,
});

console.log("Testing Gemini...");

const response = await ai.models.generateContent({
  model: "gemini-3.8-flash",
  contents: "Say hello in one sentence.",
});

console.log("Gemini response:");
console.log(response.text);