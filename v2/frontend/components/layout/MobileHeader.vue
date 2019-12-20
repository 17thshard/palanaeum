<template>
  <header class="mobile-header">
    <a @click="navigationVisible = true" class="fa fa-bars" aria-hidden="true">
      <Badge v-if="badge !== undefined" usage="icon">{{ badge }}</Badge>
    </a>
    <FlexLink class="mobile-header__logo" url="/">
      Arcanum
    </FlexLink>
    <a @click="searchVisible = !searchVisible" class="fa fa-search" aria-hidden="true" />
    <transition name="fade">
      <SearchBar v-if="searchVisible" class="mobile-header__search" />
    </transition>
    <transition name="mobile-header__drawer">
      <div v-if="navigationVisible" @click.self="navigationVisible = false" class="mobile-header__drawer">
        <div class="mobile-header__navigation">
          <a @click.prevent="navigationVisible = false" class="mobile-header__drawer-close" href="#">×</a>
          <div class="mobile-header__navigation-wrapper">
            <div class="mobile-header__navigation-overflow">
              <NavBar vertical />
              <UserBar v-if="$auth.loggedIn" vertical />
            </div>
          </div>
          <LoginBar v-if="!$auth.loggedIn" vertical show-text />
        </div>
      </div>
    </transition>
  </header>
</template>

<script>
import NavBar from '@/components/layout/NavBar.vue'
import SearchBar from '@/components/layout/SearchBar.vue'
import LoginBar from '@/components/layout/LoginBar.vue'
import FlexLink from '@/components/ui/FlexLink.vue'
import UserBar from '@/components/layout/UserBar.vue'
import Badge from '~/components/ui/Badge.vue'

export default {
  name: 'MobileHeader',
  components: { Badge, UserBar, FlexLink, LoginBar, SearchBar, NavBar },
  data () {
    return {
      navigationVisible: false,
      searchVisible: false
    }
  },
  computed: {
    badge () {
      const { loggedIn, user } = this.$auth
      return loggedIn ? user.notifications : undefined
    }
  },
  watch: {
    $route () {
      this.navigationVisible = false
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
  z-index: 2;

  @media (max-width: $medium-breakpoint) {
    display: flex;
  }

  .fa {
    position: relative;
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

  &__drawer {
    display: flex;
    align-items: stretch;
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: rgba(0, 0, 0, 0.5);

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

    &-enter-active, &-leave-active {
      transition: background .3s ease-in-out;

      .mobile-header__navigation {
        transition: transform .3s ease-in-out;
      }
    }

    &-enter, &-leave-to {
      background: rgba(0, 0, 0, 0);

      .mobile-header__navigation {
        transform: translateX(-100%);
      }
    }
  }

  &__navigation {
    display: flex;
    flex-direction: column;
    background-color: $navbar-background;
    width: 200px;
    font-size: 22px;
    line-height: 1.5;

    &-wrapper {
      display: flex;
      flex: 1;
      min-height: 0;
    }

    &-overflow {
      flex: 1;
      overflow: auto;
    }
  }
}
</style>
