/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0a0a0f",
          50: "#12121a",
          100: "#1a1a25",
          200: "#22222f",
          300: "#2a2a3a",
        },
        neon: {
          cyan: "#06d6a0",
          blue: "#4cc9f0",
          purple: "#7b61ff",
          pink: "#f72585",
        },
        glass: {
          DEFAULT: "rgba(255,255,255,0.06)",
          light: "rgba(255,255,255,0.1)",
          border: "rgba(255,255,255,0.08)",
          "border-light": "rgba(255,255,255,0.15)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(6, 214, 160, 0.15)",
        "glow-lg": "0 0 40px rgba(6, 214, 160, 0.2)",
        "glow-purple": "0 0 20px rgba(123, 97, 255, 0.15)",
        "glow-blue": "0 0 20px rgba(76, 201, 240, 0.15)",
        card: "0 4px 30px rgba(0, 0, 0, 0.3)",
      },
      animation: {
        "float": "float 6s ease-in-out infinite",
        "fade-in": "fade-in 0.5s ease-out",
        "slide-up": "slide-up 0.5s ease-out",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
