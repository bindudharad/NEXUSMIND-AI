import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        void: "#050816",
        panel: "#0B1020",
        panel2: "#10172A",
        line: "#263241",
        electric: "#3B82F6",
        cyan: "#2EE9D3",
        amber: "#F6B44B",
        signal: "#F05D5E",
        ion: "#8EE3FF",
        mint: "#7CF0A6"
      },
      boxShadow: {
        "control": "0 0 0 1px rgba(46, 233, 211, 0.14), 0 24px 80px rgba(0, 0, 0, 0.44)",
        "signal": "0 0 28px rgba(240, 93, 94, 0.2)",
        "electric": "0 0 28px rgba(59, 130, 246, 0.22)",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
