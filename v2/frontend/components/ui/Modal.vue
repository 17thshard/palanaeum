<template>
  <div @click.self="$emit('close')" class="modal">
    <div class="modal__window">
      <header class="modal__header">
        <slot name="header" />

        <button @click="$emit('close')" class="modal__close" title="Close">
          <Icon name="times" />
        </button>
      </header>
      <slot />
    </div>
  </div>
</template>

<script>
import Icon from '@/components/ui/Icon.vue'

export default {
  name: 'Modal',
  components: { Icon },
  mounted () {
    window.addEventListener('keyup', this.onKeyPress)
  },
  destroyed () {
    window.removeEventListener('keyup', this.onKeyPress)
  },
  methods: {
    onKeyPress (event) {
      // Close on escape
      if (event.keyCode === 27) {
        this.$emit('close')
      }
    }
  }
}
</script>

<style lang="scss">
.modal {
  display: flex;
  align-items: center;
  justify-content: center;
  position: fixed;
  z-index: 100;
  left: 0;
  top: 0;
  bottom: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.4);
  cursor: pointer;

  &__window {
    background: $content-background;
    padding: 16px;
    border-radius: 3px;
    box-shadow: 0 5px 16px rgba(0, 0, 0, 0.1);
    cursor: auto;
    pointer-events: auto;
  }

  &__header {
    display: flex;
    align-items: center;
    font-size: 1.5rem;
    padding-bottom: 16px;
  }

  &__close {
    background: none;
    border: none;
    font-size: 1rem;
    margin-left: auto;
    cursor: pointer;
    padding: 0;

    &:hover, &:active, &:focus {
      color: $a-hover-color;
    }
  }
}
</style>
