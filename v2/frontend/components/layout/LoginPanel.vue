<template>
  <LinkBar
    :vertical="vertical"
    :links="[
      {
        title: !showText ? 'Sign in' : undefined,
        text: showText ? 'Sign in' : undefined,
        icon: 'sign-in',
        url: '/auth/login'
      },
      {
        title: !showText ? 'Sign up' : undefined,
        text: showText ? 'Sign up' : undefined,
        icon: 'user-plus',
        url: '/auth/register/'
      }
    ]"
  />
</template>

<script>
import LinkBar from '@/components/ui/LinkBar.vue'

export default {
  name: 'LoginPanel',
  components: { LinkBar },
  props: {
    showText: {
      type: Boolean,
      default: () => false
    },
    vertical: {
      type: Boolean,
      default: () => false
    }
  }
}
</script>
