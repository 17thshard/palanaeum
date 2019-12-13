<template>
  <button :class="['button', { 'button--dark': theme === 'dark' }]" @click="$emit('click', $event)">
    <slot />
  </button>
</template>

<script>
export default {
  name: 'Button',
  props: {
    theme: {
      type: String,
      default: () => ''
    }
  }
}
</script>

<style lang="scss">
.button {
  box-shadow: none;
  user-select: none;
  border: none;
  display: inline-block;
  padding: 8px 16px;
  vertical-align: middle;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  background-color: inherit;
  text-align: center;
  cursor: pointer;
  white-space: nowrap;
  border-radius: 4px;
  -webkit-appearance: button;
  font: inherit;

  &--dark {
    background: $dark-background;
    color: $text-light;
  }
}
</style>
