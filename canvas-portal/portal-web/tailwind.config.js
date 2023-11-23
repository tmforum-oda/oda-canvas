/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        customFFF: '#fff',
        label: '#909090',
        labelVal: '#646464',
      },
      fontFamily: {
        custom: ['Helvetica Neue', 'Helvetica', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '\\\\5FAE\\8F6F\\96C5\\9ED1', 'Arial', 'sans-serif']
      }
    },
  },
  plugins: [],
}

