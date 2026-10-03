import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        upay: {
          bg: "#0B132B",
          card: "#111C3A",
          cardHover: "#16234A",
          border: "#1E2D56",
          yellow: "#FFC107",
          amber: "#FFB300",
          accent: "#FFD54F",
          emerald: "#10B981",
          crimson: "#EF4444",
        },
      },
    },
  },
  plugins: [],
};

export default config;
