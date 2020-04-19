<template>
  <div>
    <PageTitle>
      All events

      <template slot="actions">
        <label for="events__sort-field">Order by:</label>
        <select id="events__sort-field">
          <option>date</option>
          <option>name</option>
        </select>
        <select id="events__sort-order" aria-label="Sort order">
          <option>descending</option>
          <option>ascending</option>
        </select>
        <Button theme="secondary">
          <Icon name="plus" />
          Add event
        </Button>
      </template>
    </PageTitle>
    <ListCard class="events-list">
      <template slot="list-header">
        <Pagination :total-pages="10" />
      </template>

      <Event
        id="american-fork-high-school-signing"
        :tags="['test', 'finished']"
        :timestamp="new Date('2019-12-12')"
        name="American Fork High School Signing"
        location="American Fork, Utah"
      />
      <Event
        id="barnes-nobles-ya-podcast"
        :tags="['test', 'finished']"
        :timestamp="new Date('2019-11-27')"
        name="Barnes&Noble YA Podcast"
      />

      <template slot="list-footer">
        <Pagination :total-pages="10" />
      </template>
    </ListCard>
  </div>
</template>

<script>
import ListCard from '@/components/ui/ListCard.vue'
import Event from '@/components/Event.vue'
import PageTitle from '@/components/layout/PageTitle.vue'
import Button from '@/components/ui/Button.vue'
import Icon from '@/components/ui/Icon.vue'
import Pagination from '@/components/ui/Pagination.vue'

export default {
  head: {
    title: 'Events'
  },
  components: { Pagination, Icon, Button, PageTitle, Event, ListCard }
}
</script>

<style lang="scss">
.events-list {
  .list-card__list-header, .list-card__list-footer {
    padding: 0;
  }
}
</style>
