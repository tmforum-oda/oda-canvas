// pages/_app.js

import Layout from '../components/layout'
import { createTheme, ThemeProvider, styled } from '@mui/material/styles';

export default function MyApp({ Component, pageProps }) {
  const lightTheme = createTheme({
    palette: {
      type: 'light',
      primary: {
        main: '#0d2548',
      },
      secondary: {
        main: '#e9242c',
        light: '#a1c04e',
      },
    }
  });


return (
  <ThemeProvider theme={lightTheme}>
    <Layout>
      <Component {...pageProps} />
    </Layout>
  </ThemeProvider>
)
}