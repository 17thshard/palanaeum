<template>
  <LinkBar
    :vertical="vertical"
    :inline-dropdowns="vertical"
    :links="[
      {
        title: 'User',
        text: vertical ? 'User' : '',
        icon: 'user',
        url: '/auth/login',
        badge,
        children: links
      }
    ]"
  />
</template>

<script>
import LinkBar from '@/components/ui/LinkBar.vue'

export default {
  name: 'UserBar',
  components: { LinkBar },
  props: {
    vertical: {
      type: Boolean,
      default: () => false
    }
  },
  computed: {
    badge () {
      return window.Palanaeum.USER_BADGE
    },
    links () {
      return window.Palanaeum.USER_LINKS
    }
  }
}
</script>
