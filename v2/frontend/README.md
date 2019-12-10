# palanaeum frontend

## Build Setup

``` bash
# install dependencies
$ yarn install

# serve with hot reload at localhost:3000
$ yarn dev

# build for production and launch server
$ yarn build
$ yarn start

# generate static project
$ yarn generate
```

For detailed explanation on how things work, check out [Nuxt.js docs](https://nuxtjs.org).

## Contributing

As you can see, the technology in use is [Nuxt.js](https://nuxtjs.org), a framework built around [Vue.js](https://vuejs.org/) which enables server side rendering.

There are a few conventions in use in this repository that contributors should adhere to:
 * All styles are written in SCSS (for a new component add `lang="scss"` to the `style` section)
   * Classes are structured according to the [BEM model](http://getbem.com/introduction/)
   * Usually, a single component corresponds to one "block" in the CSS
   * SCSS hierarchy should be utilized for specifying elements (`&__element`) and modifiers (`&--modifier`)
