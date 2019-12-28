<template>
  <article :class="['entry', { 'entry--box': box }]">
    <header class="entry__header">
      <FlexLink v-if="event !== undefined" url="#" class="entry__event">
        {{ event }}
      </FlexLink>
      <FlexLink v-if="position !== undefined" url="#" class="entry__position">
        {{ `#${position}` }}
      </FlexLink>
      <ul v-if="!hideActions" class="entry__actions">
        <li>
          <a href="#">
            <Icon name="pencil-alt" />
            Edit
          </a>
        </li>
        <li>
          <a href="#">
            <Icon name="plus" />
            Save
          </a>
        </li>
        <li>
          <a href="#">
            <Icon name="share-alt" />
            Share
          </a>
        </li>
        <li>
          <a href="#">
            <Icon name="copy" />
            Copy
          </a>
        </li>
      </ul>
    </header>

    <div class="entry__content">
      <div class="entry__sources">
        <MiniPlayer url="https://wob.coppermind.net/media/sources/383/Take_Me_Away_interview_Rzkmu.mp3" />
      </div>

      <template v-for="line in lines">
        <h4 class="entry__speaker">
          {{ line.speaker }}
        </h4>
        <p v-html="line.content" class="entry__line" />
      </template>
    </div>

    <footer class="entry__footer">
      <div class="entry__tags">
        <Tag v-for="tag in tags" :tag="tag" :key="tag" />
      </div>
      <ul v-if="urlSources.length > 0" class="entry__url-sources">
        <li v-for="source in urlSources">
          <FlexLink :url="source.url" class="entry__url-source">
            {{ source.title }}
          </FlexLink>
        </li>
      </ul>
    </footer>
  </article>
</template>

<script>
import FlexLink from '@/components/ui/FlexLink.vue'
import Tag from '@/components/ui/Tag.vue'
import Icon from '~/components/ui/Icon.vue'
import MiniPlayer from '~/components/audio/MiniPlayer.vue'

export default {
  name: 'Entry',
  components: { MiniPlayer, Icon, Tag, FlexLink },
  props: {
    id: {
      type: String,
      required: true
    },
    position: {
      type: Number,
      default: () => undefined
    },
    event: {
      type: String,
      default: () => undefined
    },
    lines: {
      type: Array,
      default: () => []
    },
    tags: {
      type: Array,
      default: () => []
    },
    sources: {
      type: Array,
      default: () => []
    },
    box: {
      type: Boolean,
      default: () => false
    },
    hideActions: {
      type: Boolean,
      default: () => false
    }
  },
  computed: {
    inlineSources () {
      return this.sources.filter(s => s.type !== 'url')
    },
    urlSources () {
      return this.sources.filter(s => s.type === 'url')
    }
  }
}
</script>

<style lang="scss">
.entry {
  position: relative;
  display: flex;
  flex-direction: column;

  &--box {
    padding: 8px;
  }

  &__header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
  }

  &__event {
    flex-grow: 1;
    width: 100%;
    font-weight: bold;
  }

  &__position {
    color: rgba(0, 0, 0, 0.6);
  }

  &__actions {
    display: flex;
    align-items: center;
    margin-left: auto;
    list-style-type: none;
    color: rgba(0, 0, 0, 0.6);

    li {
      margin-right: 16px;

      &:last-child {
        margin-right: 0;
      }
    }
  }

  &__content {
    padding-top: 8px;
  }

  &__sources {
    float: right;
    clear: both;
  }

  &__speaker {
    font-weight: bold;
    font-size: 1.3em;
    font-family: 'Roboto Slab', serif;
  }

  &__line {
    margin-top: .7em;
    margin-bottom: .7em;
  }

  &__footer {
    display: flex;
  }

  &__tags {
    display: flex;

    .tag {
      margin-right: 4px;

      &:last-child {
        margin-right: 0;
      }
    }
  }

  &__url-sources {
    flex: 1;
    display: inline-block;
    list-style-type: none;
    padding: 0 0 0 16px;
    margin-left: auto;
    overflow-x: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    &:before {
      content: 'Sources: ';
    }

    li {
      display: inline;

      &:after {
        content: ',';
      }

      &:last-child {
        &:after {
          content: '';
        }
      }
    }
  }

  &__url-source {
    vertical-align: bottom;
    color: $theme-color;
    border-bottom: 1px dotted $theme-color;
  }
}
</style>
