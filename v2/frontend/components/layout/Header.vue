<template>
  <header class="header">
    <div class="header__logo">
      <a class="header__logo-link" href="/">
        <img
          id="svg-logo"
          alt="logo"
          src="https://wob.coppermind.net/media/config/arcanum-white-shapes.svg"
        ></a>
    </div>
    <div class="header__navigation">
      <LoginPanel show-text class="header__user" />
      <SearchBar class="header__searchbar" />
      <NavBar class="header__navbar" />
    </div>
    <transition name="fade">
      <div v-if="scrollPosition >= 160" class="header-topbar">
        <a class="header-topbar__logo" href="/">Arcanum</a>
        <NavBar class="header-topbar__navigation" />
        <LoginPanel class="header-topbar__user" />
        <SearchBar class="header-topbar__searchbar" />
      </div>
    </transition>
  </header>
</template>

<script>
import NavBar from '@/components/layout/NavBar.vue'
import SearchBar from '@/components/layout/SearchBar.vue'
import LoginPanel from '@/components/layout/LoginPanel.vue'

export default {
  name: 'Header',
  components: { LoginPanel, SearchBar, NavBar },
  data () {
    return {
      scrollPosition: 0
    }
  },
  mounted () {
    window.addEventListener('scroll', this.onScroll)
    this.onScroll()
  },
  destroyed () {
    window.removeEventListener('scroll', this.onScroll)
  },
  methods: {
    onScroll () {
      this.scrollPosition = window.pageYOffset || document.documentElement.scrollTop
    }
  }
}
</script>

<style lang="scss">
.header {
  font-size: 21px;
  position: relative;
  width: 100%;
  max-width: 1300px;
  height: 160px;
  color: #fff;
  border: 1px solid $navbar-background;
  border-bottom: none;
  background-color: $navbar-background;
  display: flex;

  @media (max-width: $medium-breakpoint) {
    display: none;
  }

  &__logo {
    width: 370px;
    margin-left: 2.5%;

    img {
      height: 150px;
    }

    &-link {
      padding-top: 3px;
    }
  }

  &__navigation {
    display: flex;
    align-items: center;
    flex-direction: column;
    width: 500px;
    margin-right: 2.5%;
    margin-left: auto;
  }

  &__user {
    background: $dark-background;
    font-size: 16px;
    margin-bottom: 17px;
  }

  &__searchbar, &__navbar {
    width: 100%;
  }

  &__navbar {
    padding-top: 12px;
  }

  &-topbar {
    font-size: 19px;
    position: fixed;
    z-index: 10;
    top: 0;
    display: flex;
    width: 100%;
    max-width: 1298px;
    background-color: $navbar-background;
    align-items: stretch;

    &__logo {
      font-family: optimus princeps semi bold, Arial, sans-serif !important;
      font-size: 21px;
      display: flex;
      align-items: center;
      padding: 8px 16px;

      &:hover {
        color: $text-light;
        background: $theme-color;
      }
    }

    &__navigation {
      flex-grow: 1;
      width: 100%;
    }

    &__user {
      margin-left: auto;
    }
  }
}
</style>
