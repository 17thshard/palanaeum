export default {
  mode: 'universal',
  server: {
    host: '0.0.0.0'
  },
  head: {
    title: process.env.npm_package_name || '',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { hid: 'description', name: 'description', content: process.env.npm_package_description || '' }
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css?family=Roboto:400,400i,700' },
      { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css?family=Roboto+Slab:400,700' }
    ]
  },
  loading: { color: '#ff0000' },
  css: [
    { src: 'assets/scss/transitions.scss', lang: 'scss' },
    { src: 'assets/scss/ui.scss', lang: 'scss' }
  ],
  styleResources: {
    scss: [
      'assets/scss/_variables.scss'
    ]
  },
  plugins: [],
  buildModules: [
    '@nuxtjs/style-resources',
    '@nuxtjs/eslint-module'
  ],
  modules: [
    '@nuxtjs/axios',
    '@nuxtjs/pwa',
    '@nuxtjs/font-awesome'
  ],
  axios: {
    browserBaseURL: '/'
  },
  build: {
    filenames: {
      app: ({ isDev }) => isDev ? '[name].[hash].js' : '[chunkhash].js',
      chunk: ({ isDev }) => isDev ? '[name].[hash].js' : '[chunkhash].js'
    }
  }
}
