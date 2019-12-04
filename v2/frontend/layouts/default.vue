<template>
  <div class="site-content">
    <Header />
    <main class="w3-row w3-margin-top w3-panel">
      <nuxt />
    </main>
  </div>
</template>

<script>
import Header from '~/components/layout/Header.vue'

export default {
  components: { Header }
}
</script>

<style lang="scss">
html {
  font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI',
  Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 16px;
  word-spacing: 1px;
  -ms-text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  box-sizing: border-box;
}

body {
  max-width: $max-body-width !important;
  background-color: $body-background;
  font-size: $base-font-size;
  font-family: 'Roboto', sans-serif;

  > header {
    font-size: $h2-font-size;
  }
}

*,
*:before,
*:after {
  box-sizing: border-box;
  margin: 0;
}

.site-content {
  border-style: solid;
  border-width: 1px 1px 1px 1px;
  border-color: $navbar-background;
  background-color: $content-background;
}

.button--green {
  display: inline-block;
  border-radius: 4px;
  border: 1px solid #3b8070;
  color: #3b8070;
  text-decoration: none;
  padding: 10px 30px;
}

.button--green:hover {
  color: #fff;
  background-color: #3b8070;
}

.button--grey {
  display: inline-block;
  border-radius: 4px;
  border: 1px solid #35495e;
  color: #35495e;
  text-decoration: none;
  padding: 10px 30px;
  margin-left: 15px;
}

.button--grey:hover {
  color: #fff;
  background-color: #35495e;
}

a {
  text-decoration: none;
  cursor: pointer;
}

a:focus, button:focus, input:focus, select:focus, select:focus, span:focus {
  box-shadow: $focus-shadow 0 0 8px;
}
</style>
