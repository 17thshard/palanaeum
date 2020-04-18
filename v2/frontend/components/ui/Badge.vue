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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: $text-light;
  text-align: center;
  border-style: none;
  line-height: 1;
  font-size: 0.5em;
  padding: 0.5em;
  background: #f44336;
  font-family: 'Roboto', sans-serif;
  font-weight: normal;

  &--round {
    border-radius: 1em;
  }

  &--icon {
    position: absolute;
    bottom: -1em;
    right: -1em;
    min-width: 1.8em;
  }

  &__content {
    line-height: 1;
    min-width: 1em;
  }
}
</style>
