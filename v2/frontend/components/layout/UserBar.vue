<template>
  <LinkBar
    :vertical="vertical"
    :inline-dropdowns="vertical"
    :links="[
      {
        title: 'User',
        text: vertical ? 'User' : undefined,
        icon: { name: 'user', fixedWidth: true },
        badge,
        url: '/auth/login',
        children: [
          {
            'title': 'Collections',
            'text': 'Collections',
            'icon': 'list',
            action() {
              $auth.logout()
            }
          },
          {
            'title': 'Settings',
            'text': 'Settings',
            'icon': 'cog',
            action() {
              $auth.logout()
            }
          },
          {
            'title': 'Staff CP',
            'text': 'Staff CP',
            'badge': 89,
            'icon': 'university',
            action() {
              $auth.logout()
            }
          },
          {
            'title': 'Sign out',
            'text': 'Sign out',
            'icon': 'power-off',
            action() {
              $auth.logout()
            }
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
      const { loggedIn, user } = this.$auth
      return loggedIn ? user.notifications : undefined
    }
  }
}
</script>
