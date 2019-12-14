<template>
  <span :class="['badge', `badge--${type}`, usage !== undefined ? `badge--${usage}` : undefined]">
    <span class="badge__content">
      <slot />
    </span>
  </span>
</template>

<script>
export default {
  name: 'Badge',
  props: {
    type: {
      type: String,
      default: () => 'round'
    },
    usage: {
      type: String,
      default: () => undefined
    }
  }
}
</script>

<style lang="scss">
.badge {
  color: $text-light;
  text-align: center;
  border-style: none;
  line-height: 1;
  padding: 0.5em;
  background: #f44336;

  &--round {
    border-radius: 100%;
    display: inline-flex;
    align-items: center;
    justify-content: center;

    &:after {
      content: '';
      display: block;

      /* Ensure the element is a square */
      height: 0;
      width: 100%;
      padding-bottom: 100%;
    }
  }

  &--icon {
    position: absolute;
    font-size: 0.5em;
    bottom: -1em;
    right: -1em;
    min-width: 1.8em;
    max-width: 1.8em;

    &:after {
      width: 0;
    }
  }

  &__content {
    overflow: visible;
    height: 0;

    /* Vertically center text since we set its height to 0 */
    margin-top: -1em;
  }
}
</style>
