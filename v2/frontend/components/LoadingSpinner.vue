<script>
export default {
  name: 'LoadingSpinner',
  functional: true,
  render (h, context) {
    return h('div', { ...context.data, class: ['loading-spinner', context.data.class] }, [
      h('div', { class: 'loading-spinner__circle1' }),
      h('div', { class: 'loading-spinner__circle2' })
    ])
  }
}
</script>

<style lang="scss">
.loading-spinner {
  width: 1em;
  height: 1em;
  position: relative;

  &__circle1, &__circle2 {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background-color: $theme-color;
    opacity: 0.6;
    position: absolute;
    top: 0;
    left: 0;
    animation: loading-spinner 2.0s infinite ease-in-out;
  }

  &__circle2 {
    animation-delay: -1s;
  }
}

@keyframes loading-spinner {
  0%, 100% {
    transform: scale(0.0);
  }
  50% {
    transform: scale(1.0);
  }
}
</style>
