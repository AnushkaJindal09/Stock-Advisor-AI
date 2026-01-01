/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      animation: {
        slide: "slide 4s linear infinite",
        draw: "draw 2.5s ease-out forwards", // 👈 Optional: move here also
      },
      keyframes: {
        slide: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        draw: {
          "0%": { strokeDasharray: "0, 999" },
          "100%": { strokeDasharray: "999, 0" },
        },
      },
    },
  },
  plugins: [],
}
