const unsafePatterns = [
  /diagnose me/i,
  /what disease do i have/i,
  /should i stop taking/i,
  /should i stop my medication/i,
  /change my medication/i,
  /increase my dose/i,
  /decrease my dose/i,
  /prescribe/i,
];

const urgentPatterns = [
  /chest pain/i,
  /difficulty breathing/i,
  /can't breathe/i,
  /severe bleeding/i,
  /unconscious/i,
  /loss of consciousness/i,
  /severe allergic reaction/i,
];

export interface SafetyResult {
  blocked: boolean;
  urgent: boolean;
  message?: string;
}

export function evaluateSafety(input: string): SafetyResult {
  if (urgentPatterns.some((pattern) => pattern.test(input))) {
    return {
      blocked: true,
      urgent: true,
      message:
        "Your message may describe a potentially urgent medical situation. Please seek immediate medical attention or contact the hospital's emergency service. I cannot assess emergencies or replace a clinician.",
    };
  }

  if (unsafePatterns.some((pattern) => pattern.test(input))) {
    return {
      blocked: true,
      urgent: false,
      message:
        "I can explain information already present in your hospital records, but I cannot diagnose a condition or independently change, stop, start, or prescribe medication. Please discuss medication or diagnosis decisions with your care team.",
    };
  }

  return {
    blocked: false,
    urgent: false,
  };
}