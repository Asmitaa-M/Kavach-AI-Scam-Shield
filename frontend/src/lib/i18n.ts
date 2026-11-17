import type { Lang, Level } from "./api";

export const LANGS: { code: Lang; label: string; speech: string }[] = [
  { code: "en", label: "English", speech: "en-IN" },
  { code: "ta", label: "தமிழ்", speech: "ta-IN" },
  { code: "hi", label: "हिन्दी", speech: "hi-IN" },
];
export const speechLang = (l: Lang) => LANGS.find((x) => x.code === l)!.speech;

type Dict = Record<string, Record<Lang, string>>;
export const T: Dict = {
  dashboard: { en: "Dashboard", ta: "முகப்பு", hi: "डैशबोर्ड" },
  upi: { en: "UPI check", ta: "UPI சோதனை", hi: "UPI जांच" },
  call: { en: "Call check", ta: "அழைப்பு சோதனை", hi: "कॉल जांच" },
  safeword: { en: "Family safe word", ta: "குடும்ப ரகசிய சொல்", hi: "परिवार का गुप्त शब्द" },
  investigate: { en: "Investigator", ta: "விசாரணை", hi: "जांचकर्ता" },
  alerts: { en: "Guardian alerts", ta: "பாதுகாவலர் எச்சரிக்கைகள்", hi: "संरक्षक अलर्ट" },
  history: { en: "History", ta: "வரலாறு", hi: "इतिहास" },
  settings: { en: "Settings", ta: "அமைப்புகள்", hi: "सेटिंग्स" },
  signout: { en: "Sign out", ta: "வெளியேறு", hi: "साइन आउट" },
  analyze: { en: "Check now", ta: "இப்போது சோதிக்கவும்", hi: "अभी जांचें" },
  hear: { en: "Hear warning", ta: "எச்சரிக்கையை கேளுங்கள்", hi: "चेतावनी सुनें" },
  SAFE: { en: "No scam tactics found", ta: "மோசடி அறிகுறி இல்லை", hi: "धोखाधड़ी के संकेत नहीं" },
  SUSPICIOUS: { en: "Suspicious", ta: "சந்தேகத்திற்குரியது", hi: "संदिग्ध" },
  "HIGH RISK": { en: "High risk", ta: "அதிக ஆபத்து", hi: "उच्च जोखिम" },
};
export const t = (k: string, l: Lang) => T[k]?.[l] ?? T[k]?.en ?? k;

/** Spoken verdicts. Translated by hand; the detailed reasons shown on screen remain in English. */
export function spokenWarning(level: Level, lang: Lang, upiMoneyOut: boolean): string {
  if (level === "HIGH RISK" && upiMoneyOut) {
    return {
      en: "Stop! Approving this request may send money from your bank account. Do not share your PIN or OTP.",
      ta: "நிறுத்துங்கள்! இந்த கோரிக்கையை ஏற்றால் உங்கள் வங்கிக் கணக்கிலிருந்து பணம் செல்லக்கூடும். பின் அல்லது ஓடிபி பகிராதீர்கள்.",
      hi: "रुकिए! इस अनुरोध को मंजूर करने पर आपके बैंक खाते से पैसे कट सकते हैं। अपना पिन या ओटीपी साझा न करें।",
    }[lang];
  }
  return {
    "HIGH RISK": {
      en: "Stop! This looks like a scam. Do not send money. Do not share any OTP or PIN. Call your family member on a saved number.",
      ta: "நிறுத்துங்கள்! இது மோசடியாக இருக்கலாம். பணம் அனுப்பாதீர்கள். ஓடிபி அல்லது பின் பகிராதீர்கள். சேமித்த எண்ணில் குடும்ப உறுப்பினரை அழையுங்கள்.",
      hi: "रुकिए! यह धोखाधड़ी लग रही है। पैसे न भेजें। ओटीपी या पिन साझा न करें। सहेजे हुए नंबर पर परिवार को फोन करें।",
    },
    SUSPICIOUS: {
      en: "Be careful. This looks suspicious. Check with someone you trust before you act.",
      ta: "கவனமாக இருங்கள். இது சந்தேகத்திற்குரியது. செயல்படும் முன் நம்பகமான ஒருவரிடம் சரிபார்க்கவும்.",
      hi: "सावधान रहें। यह संदिग्ध लगता है। कुछ भी करने से पहले किसी भरोसेमंद व्यक्ति से पूछ लें।",
    },
    SAFE: {
      en: "No scam tactics were found. Stay alert anyway.",
      ta: "மோசடி அறிகுறிகள் எதுவும் இல்லை. இருந்தாலும் எச்சரிக்கையாக இருங்கள்.",
      hi: "धोखाधड़ी के कोई संकेत नहीं मिले। फिर भी सतर्क रहें।",
    },
  }[level][lang];
}
