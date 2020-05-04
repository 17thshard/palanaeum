<template>
  <div class="recent-entries">
    <PageTitle>
      Recent entries

      <template slot="actions">
        <label for="recent-entries__sort-field">Order by:</label>
        <select id="recent-entries__sort-field">
          <option>creation date</option>
          <option>modification date</option>
          <option>recording date</option>
        </select>
        <nuxt-link class="page-title__icon-link" to="feed" append title="Feed">
          <Icon name="rss" />
        </nuxt-link>
      </template>
    </PageTitle>
    <ListCard class="recent-entries__list">
      <Entry
        :position="1"
        :entry="{
          id: 1,
          lines: [
            { speaker: 'Questioner', content: 'My question has to do with the color of Shallan\'s eyes currently, because we\'ve noticed over the books that Kaladin\'s eyes, as he\'s continued to use his Surge, changed to lighter and lighter blue. Whereas one could argue that Shallan is farther in her Ideals than Kaladin is, yet her eyes have not changed at all.' },
            { speaker: 'Brandon Sanderson', content: 'Right, \'cause they were already light.' }
          ],
          tags: ['rafo', 'roshar', 'surgebinding'],
          sources: [
            {type: 'url', url: 'https://youtu.be/wfd5zIA0SYU', title: 'The Brandon and Dan Show at Life, the Universe and Everything'},
            {type: 'url', url: 'https://youtu.be/wfd5zIA0SYU', title: 'The Brandon and Dan Show at Life, the Universe and Everything'}
          ]
        }"
        box
      />
      <Entry
        :position="1"
        :entry="{
          id: 1,
          lines: [
            { speaker: 'Questioner', content: 'My question has to do with the color of Shallan\'s eyes currently, because we\'ve noticed over the books that Kaladin\'s eyes, as he\'s continued to use his Surge, changed to lighter and lighter blue. Whereas one could argue that Shallan is farther in her Ideals than Kaladin is, yet her eyes have not changed at all.' },
            { speaker: 'Brandon Sanderson', content: 'Right, \'cause they were already light.' }
          ],
          tags: ['rafo', 'roshar', 'surgebinding'],
          sources: [
            {type: 'url', url: 'https://youtu.be/wfd5zIA0SYU', title: 'The Brandon and Dan Show at Life, the Universe and Everything'},
            {type: 'url', url: 'https://youtu.be/wfd5zIA0SYU', title: 'The Brandon and Dan Show at Life, the Universe and Everything'}
          ]
        }"
        box
      />

      <template slot="list-footer">
        <Pagination :total-pages="10" />
      </template>
    </ListCard>
  </div>
</template>

<script>
import ListCard from '@/components/ui/ListCard.vue'
import Entry from '@/components/Entry.vue'
import PageTitle from '@/components/layout/PageTitle.vue'
import Icon from '@/components/ui/Icon.vue'
import Pagination from '@/components/ui/Pagination.vue'

export default {
  head: {
    title: 'Recent entries'
  },
  components: { Pagination, Icon, PageTitle, Entry, ListCard }
}
</script>

<style lang="scss">
.recent-entries__list {
  .list-card__list {
    padding-top: 10px;
    border-left: none;
    border-right: none;
  }

  .list-card__list-header, .list-card__list-footer {
    padding: 0;
  }

  .entry {
    margin-bottom: 10px;
  }
}
</style>
