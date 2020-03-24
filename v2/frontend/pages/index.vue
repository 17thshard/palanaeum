<template>
  <GridContainer>
    <GridCell :width="12" class="welcome-card">
      <Card>
        <template slot="header">
          <Icon name="home" />
          Welcome
        </template>

        Welcome to Arcanum, the Brandon Sanderson Archive. We're here to collect everything Brandon ever says about his books&mdash;the
        "Words
        of Brandon," as they are called&mdash;with a focus on collecting information related to the cosmere.
      </Card>
    </GridCell>
    <GridCell :width="12">
      <Card>
        <template slot="header">
          <Icon name="dice" />
          Random entry
        </template>

        <Entry
          id="löllinger"
          :tags="['rafo', 'roshar', 'surgebinding']"
          :lines="[
            { speaker: 'Questioner', content: 'My question has to do with the color of Shallan\'s eyes currently, because we\'ve noticed over the books that Kaladin\'s eyes, as he\'s continued to use his Surge, changed to lighter and lighter blue. Whereas one could argue that Shallan is farther in her Ideals than Kaladin is, yet her eyes have not changed at all.' },
            { speaker: 'Brandon Sanderson', content: 'Right, \'cause they were already light.' }
          ]"
          :sources="[
            {type: 'url', url: 'https://youtu.be/wfd5zIA0SYU', title: 'The Brandon and Dan Show at Life, the Universe and Everything'}
          ]"
          event="löllinger"
          hide-actions
        />
      </Card>
    </GridCell>
    <GridCell :width="9">
      <ListCard>
        <template slot="header">
          <Icon name="newspaper" />
          Newest Events
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
          Go to full list of events >>
        </template>
      </ListCard>
    </GridCell>
    <GridCell :width="3">
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

      <ListCard>
        <template slot="header">
          <Icon name="chart-bar" />
          Statistics
        </template>

        <Statistic :value="12904" singular="entry" plural="entries" />
        <Statistic :value="375" singular="event" plural="events" />
        <Statistic :value="360" singular="audio source" plural="audio sources" />
      </ListCard>

      <ListCard>
        <template slot="header">
          <Icon name="globe" />
          Related sites
        </template>

        <NewSource name="CBE35F41-4C0D-4446-826C-FDD4752C8902.jpeg" event="American Fork High School Signing" />
        <NewSource type="audio" name="2019-11-26 - Short Isaac QA (R'Shara).mp3" event="Starsight Release Party" />
        <NewSource type="audio" name="Brandon_Sanderson_YA_Podcast__CpXJy.mp3" event="Barnes&Noble YA Podcast" />
        <NewSource type="audio" name="Take_Me_Away_interview_Rzkmu.m4a" event="Miscellaneous 2019" />
        <NewSource name="2CA171D4-DB30-4FA6-9764-E06D4E171784.jpeg" event="Starsight Release Party" />
      </ListCard>
    </GridCell>
  </GridContainer>
</template>

<script>
import Card from '@/components/ui/Card.vue'
import GridCell from '@/components/ui/GridCell.vue'
import Event from '@/components/Event.vue'
import NewSource from '@/components/pages/index/NewSource.vue'
import ListCard from '@/components/ui/ListCard.vue'
import Statistic from '@/components/pages/index/Statistic.vue'
import GridContainer from '@/components/ui/GridContainer.vue'
import Icon from '@/components/ui/Icon.vue'
import Entry from '~/components/Entry.vue'

export default {
  components: { Entry, Icon, GridContainer, Statistic, ListCard, NewSource, Event, GridCell, Card }
}
</script>
