export default {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    theme: {
      extend: {
        animation: {
          'gradient-x': 'gradientX 8s ease infinite',
        },
        keyframes: {
          gradientX: {
            '0%, 100%': {
              backgroundPosition: '0% 50%',
            },
            '50%': {
              backgroundPosition: '100% 50%',
            },
          },
        },
        backgroundSize: {
          '400': '400% 400%',
        },
      },
    },
    plugins: [],
  }