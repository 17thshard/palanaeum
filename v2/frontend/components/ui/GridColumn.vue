<template>
  <div :class="['grid-col', `grid-col--width-${width}`, { 'grid-col--centered': center }]">
    <slot />
  </div>
</template>

<script>
export default {
  name: 'GridColumn',
  props: {
    width: {
      type: Number,
      required: true
    },
    center: {
      type: Boolean,
      default: () => false
    }
  }
}
</script>

<style lang="scss">
.grid-col {
  padding: 0 16px;

  @for $i from 1 through 12 {
    &--width-#{$i} {
      width: 100% / 12 * $i;
    }
  }

  &--centered {
    margin: 0 auto;
  }

  & > * {
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }
  }
}
</style>
