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
        children: [
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
  }
}
</script>
