
const unsafePatterns = [
  /diagnose me/i,
  /what disease do i have/i,
  /should i stop taking/i,
  /should i stop my medication/i,
  /change my medication/i,
  /increase my dose/i,
  /decrease my dose/i,
  /prescribe/i,

  // Basic Amharic phrase coverage; not comprehensive.
  /በሽታዬ ምንድን ነው/,
  /መድሃኒቴን ማቆም/,
  /መድሃኒቴን መቀየር/,
  /መድሃኒቴን መጨመር/,
  /መድሃኒቴን መቀነስ/,
];

const urgentPatterns = [
  /chest pain/i,
  /difficulty breathing/i,
  /can't breathe/i,
  /cannot breathe/i,
  /severe bleeding/i,
  /unconscious/i,
  /loss of consciousness/i,
  /severe allergic reaction/i,

  // Basic Amharic phrase coverage; not comprehensive.
  /የደረት ህመም/,
  /መተንፈስ መቸገር/,
  /መተንፈስ አለመቻል/,
  /ከባድ ደም መፍሰስ/,
  /ራስን መሳት/,
];

export interface SafetyResult {
  blocked: boolean;
  urgent: boolean;
  message?: string;
}

export function evaluateSafety(
  input: string,
  language: "en" | "am" = "en"
): SafetyResult {
  const isAmharic = language === "am";

  // Urgent symptoms take priority over other pattern matches.
  if (urgentPatterns.some((pattern) => pattern.test(input))) {
    return {
      blocked: true,
      urgent: true,
      message: isAmharic
        ? "መልዕክትዎ አስቸኳይ የሕክምና ሁኔታን ሊያመለክት ይችላል። እባክዎ ወዲያውኑ የሕክምና እርዳታ ያግኙ ወይም የሆስፒታሉን የድንገተኛ አገልግሎት ያነጋግሩ። እኔ የድንገተኛ ሁኔታን መገምገም ወይም የሐኪምን እርዳታ መተካት አልችልም።"
        : "Your message may describe a potentially urgent medical situation. Please seek immediate medical attention or contact the hospital's emergency service. I cannot assess emergencies or replace a clinician.",
    };
  }

  if (unsafePatterns.some((pattern) => pattern.test(input))) {
    return {
      blocked: true,
      urgent: false,
      message: isAmharic
        ? "በሆስፒታል መዝገብዎ ውስጥ ያለውን መረጃ ማብራራት እችላለሁ፤ ነገር ግን በሽታን መመርመር ወይም መድሃኒት በራሴ መጀመር፣ ማቆም፣ መቀየር ወይም መድኃኒት ማዘዝ አልችልም። እባክዎ የምርመራ ወይም የመድሃኒት ውሳኔዎችን ከሕክምና ቡድንዎ ጋር ይወያዩ።"
        : "I can explain information already present in your hospital records, but I cannot diagnose a condition or independently change, stop, start, or prescribe medication. Please discuss medication or diagnosis decisions with your care team.",
    };
  }

  return {
    blocked: false,
    urgent: false,
  };
}
