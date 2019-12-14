<template>
  <LinkBar
    :display-icons="vertical"
    :vertical="vertical"
    :links="links"
  />
</template>

<script>
import LinkBar from '@/components/ui/LinkBar.vue'

export default {
  name: 'NavBar',
  components: { LinkBar },
  props: {
    vertical: {
      type: Boolean,
      default: () => false
    }
  },
  computed: {
    links () {
      return window.Palanaeum.NAVBAR_LINKS
    }
  }
}
</script>
