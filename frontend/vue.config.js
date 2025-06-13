const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  outputDir: 'dist',
  publicPath: '/aetheronepysocial/',
  devServer: {
    historyApiFallback: {
      index: '/aetheronepysocial/index.html'
    },
    port: 8080,
    proxy: {
      '/aetheronepysocial': {
        target: 'http://127.0.0.1:7000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
