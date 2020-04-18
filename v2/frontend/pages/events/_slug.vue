<template>
  <GridContainer>
    <GridCell :width="12">
      <PageTitle>
        State of the Sanderson 2019

        <template slot="actions">
          <Icon name="rss" />
        </template>
      </PageTitle>
    </GridCell>
    <GridCell :width="9">
      <TabNav
        :tabs="[
          { to: 'entries', title: 'Entries', append: $route.name === 'events-slug', aliases: [ 'events-slug' ] },
          { to: 'sources', title: 'Sources', append: $route.name === 'events-slug' }
        ]"
      />
      <nuxt-child class="event__child" />
    </GridCell>
    <GridCell :width="3">
      <GridContainer class="event__sidebar">
        <GridCell :width="12">
          <table class="event__overview">
            <caption>Event details</caption>
            <tbody>
              <tr>
                <th>Name</th>
                <td>State of the Sanderson 2019</td>
              </tr>
              <tr>
                <th>Date</th>
                <td>Dec. 19, 2019</td>
              </tr>
              <tr>
                <th>Entries</th>
                <td>10</td>
              </tr>
            </tbody>
          </table>
        </GridCell>
        <GridCell :width="12">
          <Button theme="secondary">
            <Icon name="pencil-alt" />
            Add entry
          </Button>
        </GridCell>
        <GridCell :width="12">
          <Button theme="secondary">
            <Icon name="upload" />
            Upload sources
          </Button>
        </GridCell>
        <GridCell :width="6">
          <Button>
            <Icon name="chevron-left" />
            Previous event
          </Button>
        </GridCell>
        <GridCell :width="6">
          <Button>
            Next event
            <Icon name="chevron-right" />
          </Button>
        </GridCell>
      </GridContainer>
    </GridCell>
  </GridContainer>
</template>

<script>
import GridCell from '@/components/ui/GridCell.vue'
import PageTitle from '@/components/layout/PageTitle.vue'
import GridContainer from '@/components/ui/GridContainer.vue'
import TabNav from '@/components/ui/TabNav.vue'
import Button from '@/components/ui/Button.vue'
import Icon from '@/components/ui/Icon.vue'

export default {
  components: { Icon, Button, TabNav, GridContainer, PageTitle, GridCell }
}
</script>

<style lang="scss">
.event__child {
  padding-top: 10px;
}

.event__sidebar {
  position: sticky;
  top: 60px;
  display: grid;
  grid-template-columns: auto;
  align-items: stretch;
  grid-gap: 16px;
}

.event__overview {
  width: 100%;
  border-collapse: collapse;

  caption {
    background: $light-background;
    padding: 8px 16px;
    color: $text-light;
  }

  tr {
    background: #f1f1f1;
    border: 1px solid #ddd;
  }

  th, td {
    padding: 8px 16px;
    text-align: left;
  }
}
</style>
