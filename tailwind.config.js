module.exports = {
  corePlugins: { preflight: false },
  content: [
    './guess_movie/quizz/templates/**/*.html',
    './guess_movie/lyrizz/templates/**/*.html',
    './guess_movie/quizz/static/**/*.js',
    './guess_movie/lyrizz/static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        bg:            '#0d0d12',
        surface:       '#15151e',
        surface2:      '#1e1e2b',
        accent:        '#e63950',
        'accent-dark': '#7a1a27',
        border:        '#25253a',
        muted:         '#7a7a90',
        good:          '#4ade80',
        bad:           '#f87171',
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
    },
  },
}
