<template>
  <LinkBar
    :links="[
      { text: 'Events', href: '/events/' },
      { text: 'Recent', href: '/recent/' },
      { text: 'Tags', href: '/tags/' },
      { text: 'Wiki', href: 'https://coppermind.net/', target: '_blank' },
      { text: 'Chat', href: 'https://discord.gg/DUMHAVV', target: '_blank' }
    ]"
  />
</template>

<script>
import LinkBar from '@/components/ui/LinkBar.vue'

export default {
  name: 'NavBar',
  components: { LinkBar }
}
</script>

<style lang="scss">
.navigation-bar {
  font-family: 'Roboto Slab', serif;
  display: flex;
  align-items: stretch;

  &__links {
    list-style-type: none;
    display: flex;
    align-items: stretch;
    margin: 0;
    padding: 0;

    li {
      display: flex;
      align-items: stretch;
    }
  }

  &__link {
    display: flex;
    align-items: center;
    padding: 8px 16px;

    &:hover {
      color: $text-light;
      background: $theme-color;
    }
  }
}
</style>
