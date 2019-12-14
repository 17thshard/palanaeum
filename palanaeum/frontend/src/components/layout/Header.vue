<template>
  <header ref="container" class="header">
    <div class="header__logo">
      <a class="header__logo-link" href="/">
        <img
          alt="logo"
          :src="logoUrl"
        >
      </a>
    </div>
    <div class="header__navigation">
      <LoginBar v-if="!loggedIn" show-text class="header__login" />
      <SearchBar class="header__searchbar" />
      <div class="header__navbar">
        <NavBar />
        <UserBar v-if="loggedIn" class="header__user" />
      </div>
    </div>
    <transition name="fade">
      <div v-if="scrollPosition >= 160" class="header-topbar">
        <a class="header-topbar__logo" href="/">
          {{ pageTite }}
        </a>
        <NavBar class="header-topbar__navigation" />
        <LoginBar v-if="!loggedIn" class="header-topbar__user" />
        <UserBar v-else class="header-topbar__user" />
        <SearchBar class="header-topbar__searchbar" />
      </div>
    </transition>
  </header>
</template>

<script>
import NavBar from '@/components/layout/NavBar.vue'
import SearchBar from '@/components/layout/SearchBar.vue'
import LoginBar from '@/components/layout/LoginBar.vue'
import UserBar from '@/components/layout/UserBar.vue'

export default {
  name: 'Header',
  components: { UserBar, LoginBar, SearchBar, NavBar },
  data () {
    return {
      scrollPosition: 0
    }
  },
  computed: {
    pageTite () {
      return window.Palanaeum.PAGE_TITLE
    },
    loggedIn () {
      return window.Palanaeum.USER_AUTHENTICATED
    },
    logoUrl () {
      return window.Palanaeum.LOGO_URL
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
  },
  provide () {
    const self = this
    return {
      dropdownBounds () {
        return self.$refs.container.getBoundingClientRect()
      }
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
      display: block;
      line-height: 1;
    }
  }

  &__navigation {
    display: flex;
    align-items: center;
    flex-direction: column;
    justify-content: flex-end;
    min-width: 500px;
    max-width: 50%;
    margin-right: 2.5%;
    margin-left: auto;
    padding-bottom: 8px;
  }

  &__login {
    background: $dark-background;
    font-size: 16px;
    margin-bottom: 17px;
  }

  &__searchbar, &__navbar {
    width: 100%;
  }

  &__navbar {
    display: flex;
    align-self: stretch;
    padding-top: 12px;
  }

  &__user {
    margin-left: auto;
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
