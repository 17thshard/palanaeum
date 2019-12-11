<template>
  <header class="mobile-header">
    <a @click="navigationVisible = true" class="fa fa-navicon" aria-hidden="true" />
    <a class="mobile-header__logo" href="/">Arcanum</a>
    <a @click="searchVisible = !searchVisible" class="fa fa-search" aria-hidden="true" />
    <transition name="fade">
      <SearchBar v-if="searchVisible" class="mobile-header__search" />
    </transition>
    <transition name="mobile-header__navigation">
      <div v-if="navigationVisible" class="mobile-header__navigation">
        <a @click.prevent="navigationVisible = false" class="mobile-header__navigation-close" href="#">×</a>
        <div class="mobile-header__navigation-wrapper">
          <div class="mobile-header__navigation-overflow">
            <NavBar vertical />
            <LoginPanel vertical show-text />
          </div>
        </div>
      </div>
    </transition>
  </header>
</template>

<script>
import NavBar from '@/components/layout/NavBar.vue'
import SearchBar from '@/components/layout/SearchBar.vue'
import LoginPanel from '@/components/layout/LoginPanel.vue'

export default {
  name: 'MobileHeader',
  components: { LoginPanel, SearchBar, NavBar },
  data () {
    return {
      navigationVisible: false,
      searchVisible: false
    }
  }
}
</script>

<style lang="scss">
.mobile-header {
  font-size: 28px;
  position: fixed;
  width: 100%;
  color: #fff;
  border-bottom: none;
  background-color: $navbar-background;
  padding: 8px 16px;
  display: none;
  align-items: center;
  flex-wrap: wrap;
  top: 0;
  line-height: 1;

  @media (max-width: $medium-breakpoint) {
    display: flex;
  }

  &__logo {
    font-size: 26px;
    font-family: optimus princeps semi bold, Arial, sans-serif !important;
    margin: 0 auto;
  }

  &__search {
    width: 100%;
    padding: 8px 0 0;
    font-size: 14px;
    line-height: 1.5;
  }

  &__navigation {
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    background-color: $navbar-background;
    width: 200px;
    font-size: 22px;
    line-height: 1.5;

    &-close {
      display: block;
      padding: 8px 16px;
      vertical-align: middle;
      white-space: nowrap;
      user-select: none;
      align-self: flex-start;

      &:hover {
        color: $text-light;
        background: $theme-color;
      }
    }

    &-wrapper {
      display: flex;
      flex: 1;
      min-height: 0;
    }

    &-overflow {
      flex: 1;
      overflow: auto;
    }

    &-enter-active, &-leave-active {
      transition: transform .5s;
    }

    &-enter, &-leave-to {
      transform: translateX(-100%);
    }
  }
}
</style>
