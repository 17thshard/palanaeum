<template>
  <LinkBar
    :vertical="vertical"
    :links="[
      {
        text: 'Discover',
        children: [
          { text: 'Events', url: '/events/' },
          { text: 'Recent', url: '/recent/' },
          { text: 'Tags', url: '/tags/' },
          { text: 'Tags', url: '/random/' },
          { text: 'Readings', url: '/random/' },
          { text: 'FAQ', url: '/random/' }
        ]
      },
      {
        text: 'Contribute',
        children: [
          { text: 'Help Transcribe', url: '/events/' },
          { text: 'Editing Guide', url: '/recent/' },
          { text: 'Style Guide', url: '/tags/' }
        ]
      },
      {
        text: 'Links',
        children: [
          { text: 'Chat', url: 'https://discord.gg/DUMHAVV', target: '_blank' },
          { text: 'Forums', url: 'https://www.17thshard.com/forum/forum/89-arcanum-discussion/', target: '_blank' },
          { text: 'Wiki', url: 'https://coppermind.net/', target: '_blank' },
          { text: 'Upcoming Events', url: 'https://www.brandonsanderson.com/upcoming-events/', target: '_blank' }
        ]
      },
      {
        text: 'Help',
        children: [
          { text: 'User Guide', url: '/events/' },
          { text: 'Search', url: '/recent/' },
          { text: 'FAQ', url: '/tags/' },
          { text: 'About', url: '/tags/' },
          { text: 'Contact', url: '/tags/' }
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
