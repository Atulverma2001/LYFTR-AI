/** Design tokens: one cool-neutral palette, ink-blue accent taken from the Lyftr mark. */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F4F6FA",
        surface: "#FFFFFF",
        ink: "#0E1B3D",
        muted: "#5A6478",
        line: "#DFE4EC",
        accent: { DEFAULT: "#1D5BD6", soft: "#E7EFFC", strong: "#1649AB" },
        ok: { DEFAULT: "#17753F", soft: "#E4F4EA" },
        warn: { DEFAULT: "#9A5B06", soft: "#FBF0DC" },
        danger: { DEFAULT: "#B42318", soft: "#FCE9E7" },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: { control: "8px", panel: "14px" },
      boxShadow: { panel: "0 1px 2px rgba(14,27,61,.06)", pop: "0 8px 24px rgba(14,27,61,.12)" },
      transitionDuration: { DEFAULT: "150ms" },
    },
  },
  plugins: [],
};
