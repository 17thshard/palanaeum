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
        children: [
          {
            title: 'Staff CP',
            text: 'Staff CP',
            icon: 'university',
            badge,
            url: '/auth/logout'
          },
          {
            title: 'Sign out',
            text: 'Sign out',
            icon: 'power-off',
            url: '/auth/logout'
          }
        ]
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
    }
  }
}
</script>
