<template>
  <div :class="['grid-cell', `grid-cell--width-${width}`, `grid-cell--start-${start}`]">
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
    start: {
      type: Number,
      default: () => 0
    }
  }
}
</script>

<style lang="scss">
.grid-cell {
  position: relative;

  @for $i from 1 through $grid-units {
    &--start-#{$i} {
      grid-column-start: $i;
    }

    &--width-#{$i} {
      grid-column-end: span $i;
    }
  }

  & > * {
    width: 100%;
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
