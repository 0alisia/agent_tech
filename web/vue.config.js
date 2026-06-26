module.exports = {
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        changeOrigin: true,
        target: 'http://127.0.0.1:8000'
      },
      '/media': {
        changeOrigin: true,
        target: 'http://127.0.0.1:8000'
      }
    }
  }
}
