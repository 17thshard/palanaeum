<template>
  <span
    :class="[
      'icon',
      type === 'regular' ? 'far' : 'fa',
      `fa-${name}`,
      { 'fa-fw': fixedWidth }
    ]"
    aria-hidden="true"
  >
    <slot />
  </span>
</template>

<script>
export default {
  name: 'Icon',
  props: {
    name: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: () => 'solid'
    },
    fixedWidth: {
      type: Boolean,
      default: () => false
    }
  }
}
</script>

<style lang="scss">
.icon {
  position: relative;
}
</style>
