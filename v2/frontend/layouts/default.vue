<template>
  <div class="site">
    <Header />
    <MobileHeader />
    <main class="site__content">
      <nuxt />
    </main>
    <footer class="site__footer">
      Powered by Palanaeum (1.1.0)
    </footer>
    <notifications class="site__notifications" classes="site__notification" position="bottom right" />
  </div>
</template>

<script>
import Header from '@/components/layout/Header.vue'
import MobileHeader from '@/components/layout/MobileHeader.vue'

export default {
  components: { MobileHeader, Header }
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

  @media (max-width: $medium-breakpoint) {
    padding-top: 40px;
  }

  &__content {
    position: relative;
    padding: 16px;
    border: 1px solid $navbar-background;
    border-top: none;
    background-color: $content-background;
  }

  &__footer {
    text-align: center;
    color: #757575;
    padding: 8px 0;
  }

  &__notifications {
    display: block;
    position: fixed;
    z-index: 5000;
  }

  .vue-notification-wrapper {
    display: block;
    overflow: hidden;
    width: 100%;
    margin: 0;
    padding: 0 16px 0 0;

    &:last-child {
      padding-bottom: 16px;
    }
  }

  &__notification {
    display: block;
    box-sizing: border-box;
    font-size: 1rem;
    padding: 8px 16px;
    margin: 0 5px 5px;
    color: #fff;
    background: #44a4fc;
    border-left: 5px solid #187fe7;
    cursor: pointer;

    &.warn {
      background: #ffb648;
      border-left-color: #f48a06
    }

    &.error {
      background: #e54d42;
      border-left-color: #b82e24
    }

    &.success {
      background: #68cd86;
      border-left-color: #42a85f;
    }
  }

  .vue-notification-title {
    font-weight: 600;
  }

  .vn-fade-enter-active, .vn-fade-leave-active, .vn-fade-move {
    transition: all .5s ease-in-out;
  }

  .vn-fade-enter, .vn-fade-leave-to {
    opacity: 0;
  }
}
</style>
