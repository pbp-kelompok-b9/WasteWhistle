module.exports = {
  content: [
    "./templates/**/*.html",
    "./*/templates/**/*.html",
    "./reporting/forms.py",
    "./static/**/*.js",
    "./*/static/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
