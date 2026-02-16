/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{html,ts}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Cabin', 'sans-serif'],
      },
      colors: {
        'ed-blue-dark': 'var(--ed-blue-dark)',
        'ed-blue': 'var(--ed-blue)',
        'ed-blue-light': 'var(--ed-blue-light)',
        'ed-yellow': 'var(--ed-yellow)',
        'ed-purple': 'var(--ed-purple)',
        'ed-background': 'var(--ed-background)',
        'ed-white': 'var(--ed-white)',
        'ed-gray-dark': 'var(--ed-gray-dark)',
        'ed-gray-text': 'var(--ed-gray-text)',
        'ed-gray-light': 'var(--ed-gray-light)',
        'ed-red': 'var(--ed-red)',
        'ed-green': 'var(--ed-green)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
