<template>
  <div class="entry-history">
    <PageTitle>Revision history</PageTitle>
    <nuxt-link to="edit" class="breadcrumb">
      <Icon name="arrow-left" />
      Back to entry editor
    </nuxt-link>
    <TabNav
      :tabs="[
        { to: '#older', title: 'Older' },
        { to: '#compare', title: 'Compare', aliases: [''] },
        { to: '#newer', title: 'Newer' },
      ]"
    />
    <client-only>
      <div class="entry-history__content">
        <transition
          name="entry-history__tab-fade"
          mode="out-in"
        >
          <Entry
            id="old"
            key="old"
            v-if="$route.hash === '#older'"
            :lines="old.lines"
            :tags="old.tags"
            :sources="old.sources"
            hide-actions
            hide-sources
          />
          <Entry
            id="new"
            key="new"
            v-else-if="$route.hash === '#newer'"
            :lines="this.new.lines"
            :tags="this.new.tags"
            :sources="this.new.sources"
            hide-actions
            hide-sources
          />
          <EntryDiff
            key="comparison"
            v-else
            :old="old"
            :new="this.new"
          />
        </transition>
      </div>
    </client-only>
  </div>
</template>

<script>
import Icon from '@/components/ui/Icon.vue'
import PageTitle from '@/components/layout/PageTitle.vue'
import EntryDiff from '@/components/EntryDiff.vue'
import TabNav from '@/components/ui/TabNav.vue'
import Entry from '@/components/Entry.vue'

export default {
  components: { Entry, TabNav, EntryDiff, PageTitle, Icon },
  head: {
    title: 'Revision history'
  },
  data () {
    return {
      old: {
        lines: [
          {
            speaker: 'The Dusty Wheel',
            content: '<p>Everyone\'s here to find out more details about what\'s going on with the state of Sanderson. What can you tell the fans that you haven\'t said yet? How are things going, what\'s in process, and what can we expect?</p>'
          },
          {
            speaker: 'Brandon Sanderson',
            content: '<p>I ended the fourth draft of <em>Rhythm of War</em> today. This is the big beta read revision. I spent the last week taking a break from <em>Rhythm of War</em> and working on the novella that\'s going to go in between books 3 and 4 (theoretically, if I actually finish it). I did one of those between books 2 and 3, and I really liked it. But I only got two chapters of that done, about 10% of it. So, who knows how long it will take me to get that finished after this is done. I\'ve got about two months of work to do this revision, and then one month left for the final polish, which will be June. Right now, just digging into that. Beta reads have given me a lot of useful feedback. A lot of things I\'m changing are just slight tonal tweaks here and there, just to balance out.</p> <p>One of the things that happens, particularly with a Stormlight book, is: I write a lot of viewpoints separately and then interweave them, and that ends up creating generally some tonal problems here and there, and some pacing problems that just need to be smoothed out. Either chapters need to be rearranged, or the tone of a chapter needs to change, because I have too many heavy tone chapters in a row and one of them needs to be lightened up, or vice versa. Things like that.</p>'
          },
          {
            speaker: 'The Dusty Wheel',
            content: '<p>Can you give the fans a hint, maybe, about character groupings? I know that\'s been a big question among the fans.</p>'
          },
          {
            speaker: 'Brandon Sanderson',
            content: '<p>I\'m not sure if I can give too much of a hint about that. What I can say is, start to make people\'s expectations: this is the Venli/Eshonai book. But really, it\'s the Venli/Eshonai flashbacks, and the main book is focusing a lot more on another character. This just naturally happened during the writing process; there was another character that ended up taking a lot of the time. It\'s not a person who has a flashback sequence in the books. So, you can theorize on who that would be; it\'s someone who does not have a flashback sequence, so it\'s not Kaladin, Shallan, Dalinar, Szeth, Eshonai. But, really, it\'s this character\'s book, mixed with flashbacks for Venli/Eshonai. It really turned into that character\'s book a lot more than I was expecting, and it was one of those happy accidents where I really liked how it turned out. But fans who go into this expecting something that\'s as much Eshonai or Venli\'s book as the last book was Dalinar\'s book are probably going to be disappointed, because it\'s more of a split between these three characters. Venli/Eshonai in the flashbacks, and then someone else in the present.</p><p>So, hardcore fans, expect another character to really be the focus of this book.</p>'
          },
          {
            speaker: 'The Dusty Wheel',
            content: '<p>Do you have a favorite you\'ve already announced that\'s in Rhythm of War that has been your favorite character to write in this book.</p>'
          },
          { speaker: 'Brandon Sanderson', content: '<p>It has been this character that I\'m not going to tell you who it is.</p>' }
        ],
        tags: ['old', 'old1'],
        sources: []
      },
      new: {
        lines: [
          {
            speaker: 'The Dusty Wheel',
            content: '<p>Everyone\'s here to find out more details about what\'s going on with the state of Sanderson. What can you tell the fans that you haven\'t said yet? How are things going, what\'s in process, and what can we expect?</p>'
          },
          {
            speaker: '<a href=\'https://twitter.com/BrandSanderson\'>Brandon Sanderson</a>',
            content: '<p>I started the fourth draft of <em>Rhythm of War</em> today. This is the big beta read revision. I spent the last week taking a break from <em>Rhythm of War</em> and working on the novella that\'s going to go in between books 3 and 4 (theoretically, if I actually finish it). I did one of those between books 2 and 3, and I really liked it. But I only got two chapters of that done, about 10% of it. So, who knows how long it will take me to get that finished after this is done. I\'ve got about two months of work to do this revision, and then one month left for the final polish, which will be June. Right now, just digging into that. Beta reads have given me a lot of useful feedback. A lot of things I\'m changing are just slight tonal tweaks here and there, just to balance out.</p> <p>One of the things that happens, particularly with a Stormlight book, is: I write a lot of viewpoints separately and then interweave them, and that ends up creating generally some tonal problems here and there, and some pacing problems that just need to be smoothed out. Either chapters need to be rearranged, or the tone of a chapter needs to change, because I have too many heavy tone chapters in a row and one of them needs to be lightened up, or vice versa. Things like that.</p>'
          },
          {
            speaker: 'The Dusty Wheel',
            content: '<p>Can you give the fans a hint, maybe, about character groupings? I know that\'s been a big question among the fans.</p>'
          },
          {
            speaker: 'Brandon Sanderson',
            content: '<p>I\'m not sure if I can give too much of a hint about that. What I can say is, start to make people\'s expectations: this is the Venli/Eshonai book. But really, it\'s the Venli/Eshonai flashbacks, and the main book is focusing a lot more on another character. This just naturally happened during the writing process; there was another character that ended up taking a lot of the time. It\'s not a person who has a flashback sequence in the books. So, you can theorize on who that would be; it\'s someone who does not have a flashback sequence, so it\'s not Kaladin, Shallan, Dalinar, Szeth, Eshonai. But, really, it\'s this character\'s book, mixed with flashbacks for Venli/Eshonai. It really turned into that character\'s book a lot more than I was expecting, and it was one of those happy accidents where I really liked how it turned out. But fans who go into this expecting something that\'s as much Eshonai or Venli\'s book as the last book was Dalinar\'s book are probably going to be disappointed, because it\'s more of a split between these three characters. Venli/Eshonai in the flashbacks, and then someone else in the present.</p><p>So, hardcore fans, expect another character to really be the focus of this book.</p>'
          },
          {
            speaker: 'The Dusty Wheel',
            content: '<p>Do you have a favorite you\'ve already announced that\'s in Rhythm of War that has been your favorite character to write in this book.</p>'
          },
          { speaker: 'Brandon Sanderson', content: '<p>It has been this character that I\'m not going to tell you who it is.</p>' }
        ],
        tags: ['old', 'new1'],
        sources: [{ type: 'url', title: 'The Dusty Wheel Livestream 2020-04-01', url: 'https://www.youtube.com/watch?v=rl3SxTPZauQ' }]
      }
    }
  }
}
</script>

<style lang="scss">
.entry-history {
  &__content {
    padding: 8px 16px;
    border: 1px solid rgba(0, 76, 110, .5);
    box-shadow: 0 1px 0 rgba(0, 76, 110, .2);
    position: relative;
  }

  &__tab-fade {
    &-enter-active, &-leave-active {
      transition: opacity 0.1s ease-in-out;
    }

    &-enter, &-leave-active {
      opacity: 0;
    }
  }
}
</style>
