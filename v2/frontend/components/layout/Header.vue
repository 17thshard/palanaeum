<template>
  <header class="header w3-hide-small w3-hide-medium">
    <div class="header__logo">
      <a href="/" class="header__logo-link w3-left"><img
        id="svg-logo"
        src="https://wob.coppermind.net/media/config/arcanum-white-shapes.svg"
        alt="logo"
      ></a>
    </div>
    <div class="header__navigation">
      <div class="header__login w3-theme-dark hidden">
        <nav class="w3-bar">
          <a class="w3-hover-theme w3-bar-item" href="/auth/login/?next=/">
            <span class="fa fa-sign-in" aria-hidden="true" />
            Sign in
          </a>
          <a class="w3-hover-theme w3-bar-item" href="/auth/register/">
            <span class="fa fa-user-plus" aria-hidden="true" />
            Sign up
          </a>
        </nav>
      </div>
      <SearchBar class="header__searchbar" />
      <NavBar class="header__navbar" />
    </div>
    <transition name="fade">
      <div v-if="scrollPosition > 150" class="header-topbar w3-bar">
        <a href="/" class="w3-left w3-hover-theme w3-bar-item logobold">Arcanum</a>
        <NavBar />
        <SearchBar class="header-topbar__searchbar" />
      </div>
    </transition>
  </header>
</template>

<script>
import NavBar from '@/components/layout/NavBar.vue'
import SearchBar from '@/components/layout/SearchBar.vue'

export default {
  name: 'Header',
  components: { SearchBar, NavBar },
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
  background-color: $navbar-background;
  color: #fff;
  width: 100%;
  max-width: 1300px;
  height: 158px;
  position: relative;

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

  .w3-bar .w3-bar-item {
    font-family: 'Roboto Slab', serif;
  }

  &__navigation {
    width: 500px;
    float: right;
    margin-right: 2.5%;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  &__login {
    font-size: 16px;
    margin-bottom: 17px;
  }

  &__searchbar {
    width: 100%;
  }

  &__navbar {
    padding-top: 12px;
  }

  &-topbar {
    position: fixed;
    display: flex;
    font-size: 19px;
    background-color: $navbar-background;
    width: 100%;
    max-width: 1298px;
    z-index: 10;
    top: 0;

    .logobold {
      font-family: optimus princeps semi bold, Arial, sans-serif !important;
      font-size: 21px;
    }

    &__searchbar {
      margin-left: auto;
    }
  }
}
</style>
