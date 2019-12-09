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
@font-face {
  font-family: "Optimus Princeps";
  src: url('~assets/fonts/OptimusPrinceps.ttf') format("truetype");
}

@font-face {
  font-family: "Optimus Princeps Semi Bold";
  src: url('~assets/fonts/OptimusPrincepsSemiBold.ttf') format("truetype");
}

html {
  font-family: 'Roboto', sans-serif;
  font-size: $base-font-size;
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
</style>
