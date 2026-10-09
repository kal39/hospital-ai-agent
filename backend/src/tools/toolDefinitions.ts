import { Type } from "@google/genai";

export const hospitalToolDefinitions = [
  {
    name: "getLatestLabResults",
    description:
      "Retrieves the authenticated patient's most recent laboratory test results, including test names, values, units, reference ranges, dates, and status.",
    parameters: {
      type: Type.OBJECT,
      properties: {},
    },
  },

  {
    name: "compareLabResults",
    description:
      "Compares the authenticated patient's latest laboratory results with previous results and identifies changes or trends.",
    parameters: {
      type: Type.OBJECT,
      properties: {},
    },
  },

  {
    name: "getMedications",
    description:
      "Retrieves the authenticated patient's currently recorded medications, including medication name, dosage, frequency, instructions, and active status.",
    parameters: {
      type: Type.OBJECT,
      properties: {},
    },
  },

  {
    name: "getMedicalHistory",
    description:
      "Retrieves the authenticated patient's recorded medical history, including visits, treatments, medication reviews, and other documented history entries.",
    parameters: {
      type: Type.OBJECT,
      properties: {},
    },
  },

  {
    name: "getPatientProfile",
    description:
      "Retrieves the authenticated patient's permitted profile information, such as basic patient information and recorded allergies.",
    parameters: {
      type: Type.OBJECT,
      properties: {},
    },
  },
];