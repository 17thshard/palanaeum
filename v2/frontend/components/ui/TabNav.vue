<template>
  <nav class="tab-nav">
    <nuxt-link
      v-for="tab in tabs"
      :key="tab.to"
      v-bind="tab"
      :class="['tab-nav__tab', { 'tab-nav__tab--active': isAliasActive(tab) }]"
      active-class="tab-nav__tab--active"
    >
      {{ tab.title }}
    </nuxt-link>
  </nav>
</template>

<script>
export default {
  name: 'TabNav',
  props: {
    tabs: {
      type: Array,
      required: true
    }
  },
  methods: {
    isAliasActive (tab) {
      if (typeof tab.to === 'string' && tab.to.charAt(0) === '#') {
        return (tab.aliases || []).includes(this.$route.hash)
      }

      return (tab.aliases || []).includes(this.$route.name)
    }
  }
}
</script>

<style lang="scss">
.tab-nav {
  display: flex;
  align-items: stretch;
  background: $light-background;
  margin-bottom: 0;

  &__tab {
    display: block;
    padding: 8px 16px;
    color: $text-light !important;
    font-family: roboto slab, serif;

    &:hover, &:active, &:focus {
      background: $theme-color;
    }

    &--active {
      background: #26364a;
    }
  }
}
</style>
