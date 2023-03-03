module.exports = {
    async rewrites() {
      return [
        {
          source: '/proxy/:path*',
          destination: 'http://localhost:8001/:path*' // Proxy to Backend
        }
      ]
    }
  }