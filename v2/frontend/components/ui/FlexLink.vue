<template>
  <component v-bind="componentConfig">
    <slot />
  </component>
</template>

<script>
export default {
  name: 'FlexLink',
  props: {
    url: {
      type: [String, Object],
      required: true
    }
  },
  computed: {
    componentConfig () {
      return typeof this.url === 'string' && this.url.match(/^https?:\/\//)
        ? { is: 'a', href: this.url }
        : { is: 'nuxt-link', to: this.url }
    }
  }
}
</script>
