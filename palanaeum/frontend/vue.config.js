const BundleTracker = require('webpack-bundle-tracker')
const path = require('path')

module.exports = {
  outputDir: './dist/',
  publicPath: process.env.NODE_ENV === 'production' ? '/collected-statics/' : 'http://127.0.0.1:9001/',

  devServer: {
    host: '0.0.0.0',
    port: '9001',
    public: '127.0.0.1:9001',
    headers: {
      'Access-Control-Allow-Origin': '*'
    }
  },

  pluginOptions: {
    'style-resources-loader': {
      preProcessor: 'scss',
      patterns: [
        path.resolve(__dirname, '../sass/_variables.scss')
      ]
    }
  },

  chainWebpack: config => {
    config.optimization
      .splitChunks(false)

    config
      .plugin('BundleTracker')
      .use(BundleTracker, [{
        path: __dirname,
        filename: './webpack-stats.json'
      }])

    config.plugins.delete('html')
    config.plugins.delete('preload')
    config.plugins.delete('prefetch')

    config.resolve.alias
      .set('__STATIC__', 'static')

    config.entryPoints.delete('app')
    config.entry('header')
      .add(path.resolve(__dirname, 'src/header.js'))
      .end()
  }
}
