<template>
  <li class="event">
    <h3 class="event__name">
      <FlexLink :url="`/events/${id}`">
        {{ name }}
        <small v-if="location !== undefined">({{ location }})</small>
      </FlexLink>
    </h3>

    <div class="event__details">
      <time :datetime="timestamp.toISOString()">{{ readableDate }}</time>

      <div v-if="tags.length > 0" class="event__tags">
        <Tag v-for="tag in tags" :tag="tag" :key="tag" />
      </div>
    </div>

    <span class="event__entry-count">
      {{ entryCount }}
    </span>
  </li>
</template>

<script>
import FlexLink from '@/components/ui/FlexLink.vue'
import Tag from '@/components/ui/Tag.vue'

export default {
  name: 'Event',
  components: { Tag, FlexLink },
  props: {
    id: {
      type: String,
      required: true
    },
    name: {
      type: String,
      required: true
    },
    location: {
      type: String,
      default: () => undefined
    },
    entryCount: {
      type: Number,
      default: () => 0
    },
    timestamp: {
      type: Date,
      required: true
    },
    tags: {
      type: Array,
      default: () => []
    }
  },
  computed: {
    readableDate () {
      const format = new Intl.DateTimeFormat(undefined, { formatMatcher: 'basic', month: 'long', day: 'numeric', year: 'numeric' })
      return format.format(this.timestamp)
    }
  }
}
</script>

<style lang="scss">
.event {
  position: relative;
  display: flex;
  flex-direction: column;
  list-style-type: none;
  padding: 8px 16px;

  &__name {
    font-weight: 400;
    padding: 0 0 10px;
    font-size: 20px;
  }

  &__details {
    display: flex;
    align-items: center;
  }

  &__tags {
    display: flex;
    margin-left: 8px;

    .tag {
      margin-right: 4px;

      &:last-child {
        margin-right: 0;
      }
    }
  }

  &__entry-count {
    position: absolute;
    right: 0;
    bottom: 0;
    display: inline-block;
    padding: 4px 8px;
    color: $text-light;
    background: $number-background;
    line-height: 1;
  }
}
</style>
