<template>
  <LinkBar
    :vertical="vertical"
    :links="[
      {
        text: 'Discover',
        children: [
          { text: 'Events', href: '/events/' },
          { text: 'Recent', href: '/recent/' },
          { text: 'Tags', href: '/tags/' },
          { text: 'Tags', href: '/random/' },
          { text: 'Readings', href: '/random/' },
          { text: 'FAQ', href: '/random/' }
        ]
      },
      {
        text: 'Contribute',
        children: [
          { text: 'Help Transcribe', href: '/events/' },
          { text: 'Editing Guide', href: '/recent/' },
          { text: 'Style Guide', href: '/tags/' }
        ]
      },
      {
        text: 'Links',
        children: [
          { text: 'Chat', href: 'https://discord.gg/DUMHAVV', target: '_blank' },
          { text: 'Forums', href: 'https://www.17thshard.com/forum/forum/89-arcanum-discussion/', target: '_blank' },
          { text: 'Wiki', href: 'https://coppermind.net/', target: '_blank' },
          { text: 'Upcoming Events', href: 'https://www.brandonsanderson.com/upcoming-events/', target: '_blank' }
        ]
      },
      {
        text: 'Help',
        children: [
          { text: 'User Guide', href: '/events/' },
          { text: 'Search', href: '/recent/' },
          { text: 'FAQ', href: '/tags/' },
          { text: 'About', href: '/tags/' },
          { text: 'Contact', href: '/tags/' }
        ]
      }
    ]"
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
  }
}
</script>
