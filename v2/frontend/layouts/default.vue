<template>
  <div class="site">
    <Header />
    <main class="site__content">
      <nuxt />
    </main>
    <footer class="site__footer">
      Powered by Palanaeum (1.1.0)
    </footer>
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
  box-sizing: border-box;
  word-spacing: 1px;
  -ms-text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  line-height: 1.5;
}

body {
  color: $text-dark;
  background-color: $body-background;
}

*,
*:before,
*:after {
  box-sizing: border-box;
  margin: 0;
}

.site {
  max-width: $max-body-width;
  margin: 0 auto;
  background-color: $content-background;

  &__content {
    padding: 16px;
    border: 1px solid $navbar-background;
    border-top: none;
  }

  &__footer {
    text-align: center;
    color: #757575;
    padding: 8px 0;
  }
}
</style>
