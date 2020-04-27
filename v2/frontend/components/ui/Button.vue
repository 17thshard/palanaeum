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

  &.button--active, &:hover, &:active, &:focus {
    background: $button1-hover;
  }

  &.button--disabled, &:disabled {
    cursor: not-allowed;
    color: rgba($text-light, 0.8);
    background: desaturate($button1-background, 50%) !important;
    pointer-events: none;
  }

  &--dark {
    background: $dark-background;
    color: $text-light;

    &.button--disabled, &:disabled {
      background: desaturate($dark-background, 50%) !important;
    }
  }

  &--secondary {
    background: $button2-background;

    &.button--active, &:hover, &:active, &:focus {
      background: $button2-hover;
    }

    &.button--disabled, &:disabled {
      background: desaturate($button2-background, 50%) !important;
    }
  }

  &--delete {
    background: $delete-button-background;

    &.button--active, &:hover, &:active, &:focus {
      background: $delete-button-hover;
    }

    &.button--disabled, &:disabled {
      background: desaturate($delete-button-background, 50%) !important;
    }
  }
}
</style>
