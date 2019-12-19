<template>
  <div :class="['grid-col', `grid-col--width-${width}`, { 'grid-col--centered': center }]">
    <slot />
  </div>
</template>

<script>
export default {
  name: 'GridCell',
  props: {
    width: {
      type: Number,
      required: true
    },
    height: {
      type: Number,
      default: () => undefined
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
  @for $i from 1 through $grid-units {
    &--width-#{$i} {
      grid-column: span $i;
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

  @media (max-width: $medium-breakpoint) {
    width: 100%;
    grid-column: 1;
  }
}
</style>
