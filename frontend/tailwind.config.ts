import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#0A1322", 900: "#0E1A2D", 800: "#13223A", 700: "#1C2F4D", 600: "#2A4166" },
        mist: { 100: "#E8EEF8", 300: "#B4C2D9", 500: "#8497B3" },
        alarm: { DEFAULT: "#FF4D5E", soft: "#3A1620" },
        amber: { DEFAULT: "#F5B544", soft: "#3A2C12" },
        safe: { DEFAULT: "#3DDC97", soft: "#10332A" },
        cyan: { DEFAULT: "#4CC9F0", soft: "#0F2F3C" },
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', '"Noto Sans Tamil"', '"Noto Sans Devanagari"', "system-ui", "sans-serif"],
        body: ['Figtree', '"Noto Sans Tamil"', '"Noto Sans Devanagari"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
