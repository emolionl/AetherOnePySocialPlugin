const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  outputDir: 'dist',
  publicPath: '/aetheronepysocialplugin/',
  devServer: {
    historyApiFallback: {
      index: '/aetheronepysocialplugin/index.html'
    },
    port: 8080,
    proxy: {
      '/aetheronepysocialplugin': {
        target: 'http://127.0.0.1:7000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
