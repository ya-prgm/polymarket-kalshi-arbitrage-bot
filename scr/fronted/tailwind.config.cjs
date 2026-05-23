/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#7367f0",
        success: "#28c76f",
        danger: "#ea5455",
        warning: "#ff9f43",
        info: "#00cfe8",
        'text-muted': "#676d7d",
        'text-main': "#d0d2d6",
      },
    },
  },
  plugins: [],
}