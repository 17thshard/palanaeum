<template>
  <button :class="['button', theme !== undefined ? `button--${theme}` : undefined]" @click="$emit('click', $event)">
    <slot />
  </button>
</template>

<script>
export default {
  name: 'Button',
  props: {
    theme: {
      type: String,
      default: () => undefined
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
  background-color: inherit;
  text-align: center;
  cursor: pointer;
  white-space: nowrap;
  border-radius: 4px;
  -webkit-appearance: button;
  font: inherit;
  background: $button1-background;
  color: $text-light;

  &:hover, &:active, &:focus {
    background: $button1-hover;
  }

  &--dark {
    background: $dark-background;
    color: $text-light;
  }

  &--secondary {
    background: $button2-background;

    &:hover, &:active, &:focus {
      background: $button2-hover;
    }
  }
}
</style>
