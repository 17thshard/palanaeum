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
  build: {
    filenames: {
      app: ({ isDev }) => isDev ? '[name].[hash].js' : '[chunkhash].js',
      chunk: ({ isDev }) => isDev ? '[name].[hash].js' : '[chunkhash].js'
    }
  },
  modules: [
    '@nuxtjs/axios',
    '@nuxtjs/auth',
    '@nuxtjs/pwa',
    '@nuxtjs/font-awesome'
  ],
  axios: {
    browserBaseURL: '/'
  },
  auth: {
    redirect: {
      login: '/auth/login'
    }
  },
  serverMiddleware: [
    {
      path: '/api/auth/login',
      handler (req, res, next) {
        let body = []
        req.on('data', (chunk) => {
          body.push(chunk)
        }).on('end', () => {
          body = Buffer.concat(body).toString()
          const data = JSON.parse(body)
          if (data.username !== 'test' || data.username !== 'test') {
            res.response = 401
            res.end(JSON.stringify({ message: 'Invalid credentials' }))
            return
          }
          res.end(JSON.stringify({ token: 'token' }))
        })
      }
    },
    {
      path: '/api/auth/logout',
      handler (req, res, next) {
        res.end(JSON.stringify({ message: 'Successfully logged out' }))
      }
    },
    {
      path: '/api/auth/user',
      handler (req, res, next) {
        const header = req.headers.authorization
        if (!header || header.split(' ')[1] !== 'token') {
          res.statusCode = 401
          res.end(JSON.stringify({ message: 'Invalid token' }))
          return
        }
        res.end(JSON.stringify({ user: { name: 'test', notifications: 2 } }))
      }
    }
  ]
}