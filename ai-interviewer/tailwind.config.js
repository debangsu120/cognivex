module.exports = {
  content: [
    "./App.{js,jsx,ts,tsx}",
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#e2e8f0",
        background: "#0B0B0C",
        backgroundLight: "#121212",
        card: "#1A1A1C",
        border: "#2A2A2C",
        surface: "#1E1E1E",
        textMuted: "#8E8E93",
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
