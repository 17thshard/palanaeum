<template>
  <GridRow>
    <GridColumn :width="9">
      <Card>
        <template slot="header">
          <span class="fa fa-newspaper-o" aria-hidden="true" />
          Newest Events
        </template>

        Welcome to Arcanum, the Brandon Sanderson Archive. We're here to collect everything Brandon ever says about his books--the "Words of
        Brandon," as they are called--with a focus on collecting information related to the cosmere.
      </Card>
    </GridColumn>
    <GridColumn :width="3">
      <Card>
        <template slot="header">
          <span class="fa fa-home" aria-hidden="true" />
          Welcome
        </template>

        Welcome to Arcanum, the Brandon Sanderson Archive. We're here to collect everything Brandon ever says about his books--the "Words of
        Brandon," as they are called--with a focus on collecting information related to the cosmere.
      </Card>
      <Card>
        <template slot="header">
          <span class="fa fa-home" aria-hidden="true" />
          Welcome
        </template>

        Welcome to Arcanum, the Brandon Sanderson Archive. We're here to collect everything Brandon ever says about his books--the "Words of
        Brandon," as they are called--with a focus on collecting information related to the cosmere.
      </Card>
      <Card>
        <template slot="header">
          <span class="fa fa-home" aria-hidden="true" />
          Welcome
        </template>

        Welcome to Arcanum, the Brandon Sanderson Archive. We're here to collect everything Brandon ever says about his books--the "Words of
        Brandon," as they are called--with a focus on collecting information related to the cosmere.
      </Card>
      <Card>
        <template slot="header">
          <span class="fa fa-home" aria-hidden="true" />
          Welcome
        </template>

        Welcome to Arcanum, the Brandon Sanderson Archive. We're here to collect everything Brandon ever says about his books--the "Words of
        Brandon," as they are called--with a focus on collecting information related to the cosmere.
      </Card>
      <Card>
        <template slot="header">
          <span class="fa fa-home" aria-hidden="true" />
          Welcome
        </template>

        Welcome to Arcanum, the Brandon Sanderson Archive. We're here to collect everything Brandon ever says about his books--the "Words of
        Brandon," as they are called--with a focus on collecting information related to the cosmere.
      </Card>
      <Card>
        <template slot="header">
          <span class="fa fa-home" aria-hidden="true" />
          Welcome
        </template>

        Welcome to Arcanum, the Brandon Sanderson Archive. We're here to collect everything Brandon ever says about his books--the "Words of
        Brandon," as they are called--with a focus on collecting information related to the cosmere.
      </Card>
      <Card>
        <template slot="header">
          <span class="fa fa-home" aria-hidden="true" />
          Welcome
        </template>

        Welcome to Arcanum, the Brandon Sanderson Archive. We're here to collect everything Brandon ever says about his books--the "Words of
        Brandon," as they are called--with a focus on collecting information related to the cosmere.
      </Card>
    </GridColumn>
  </GridRow>
</template>

<script>
import Card from '~/components/ui/Card.vue'
import GridColumn from '@/components/ui/GridColumn.vue'
import GridRow from '@/components/ui/GridRow.vue'

export default {
  components: { GridRow, GridColumn, Card }
}
</script>
