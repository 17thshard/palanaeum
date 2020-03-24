<template>
  <GridContainer>
    <GridCell :width="12">
      <PageTitle>
        State of the Sanderson 2019
      </PageTitle>
    </GridCell>
    <GridCell :width="9">
      <TabNav
        :tabs="[
          { to: 'entries', title: 'Entries', append: this.$route.name === 'events-slug' },
          { to: 'sources', title: 'Sources', append: this.$route.name === 'events-slug' }
        ]"
      />
      <nuxt-child class="event__child" />
    </GridCell>
    <GridCell :width="3">
      <div class="event__sidebar">
        <ListCard>
          <template slot="header">
            <Icon name="bolt" />
            New sources
          </template>

          <NewSource name="CBE35F41-4C0D-4446-826C-FDD4752C8902.jpeg" event="American Fork High School Signing" />
          <NewSource type="audio" name="2019-11-26 - Short Isaac QA (R'Shara).mp3" event="Starsight Release Party" />
          <NewSource type="audio" name="Brandon_Sanderson_YA_Podcast__CpXJy.mp3" event="Barnes&Noble YA Podcast" />
          <NewSource type="audio" name="Take_Me_Away_interview_Rzkmu.m4a" event="Miscellaneous 2019" />
          <NewSource name="2CA171D4-DB30-4FA6-9764-E06D4E171784.jpeg" event="Starsight Release Party" />
        </ListCard>
      </div>
    </GridCell>
  </GridContainer>
</template>

<script>
import GridCell from '@/components/ui/GridCell.vue'
import PageTitle from '@/components/layout/PageTitle.vue'
import NewSource from '@/components/pages/index/NewSource.vue'
import ListCard from '@/components/ui/ListCard.vue'
import GridContainer from '@/components/ui/GridContainer.vue'
import Icon from '@/components/ui/Icon.vue'
import TabNav from '@/components/ui/TabNav.vue'

export default {
  components: { TabNav, Icon, GridContainer, ListCard, NewSource, PageTitle, GridCell }
}
</script>

<style lang="scss">
.event__sidebar {
  position: sticky;
  top: 55px;
}

.event__child {
  padding-top: 10px;
}
</style>
