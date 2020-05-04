<template>
  <article :class="['entry', { 'entry--box': box, 'entry--highlighted': highlighted, 'entry--suggestion': entry.suggestion }]">
    <client-only>
      <a :name="anchor" class="entry__anchor" />
    </client-only>
    <header class="entry__header">
      <FlexLink v-if="event !== undefined" url="#" class="entry__event">
        {{ event }}
      </FlexLink>
      <FlexLink v-if="position !== undefined" :url="`#${anchor}`" class="entry__position">
        {{ `#${position}` }}
      </FlexLink>
      <ul v-if="!hideActions" class="entry__actions">
        <li>
          <nuxt-link to="/entry/1/edit">
            <Icon name="pencil-alt" />
            Edit
          </nuxt-link>
        </li>
        <li>
          <a @click.prevent="collectionsVisible = true" href="#">
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
          <a @click.prevent="copyLines" href="#">
            <Icon name="copy" />
            Copy
          </a>
        </li>
      </ul>
      <nuxt-link v-if="entry.suggestion" :to="{ name: 'entry-id-history', params: { id: entry.id } }" class="entry__suggestion-marker">
        Suggestion
      </nuxt-link>
    </header>

    <div class="entry__content">
      <div v-if="!hideSources" class="entry__sources">
        <MiniPlayer url="https://wob.coppermind.net/media/sources/383/Take_Me_Away_interview_Rzkmu.mp3" />
      </div>

      <div ref="lines" class="entry__lines">
        <template v-for="line in entry.lines">
          <h4 v-html="line.speaker" class="entry__speaker" />
          <div v-html="line.content" class="entry__line" />
        </template>
      </div>
    </div>

    <footer class="entry__footer">
      <small ref="footnote" v-if="entry.footnote" v-html="`Footnote: ${entry.footnote}`" class="entry__footnote" />
      <div class="entry__tags">
        <Tag v-for="tag in entry.tags" :tag="tag" :key="tag" />
      </div>
      <ul v-if="urlSources.length > 0" class="entry__url-sources">
        <li>Sources:</li>
        <li v-for="(source, index) in urlSources" class="entry__url-sources-item">
          <FlexLink :url="source.url" class="entry__url-source">
            <span>{{ source.title }}</span>
          </FlexLink>
          {{ urlSources.length - 1 > index ? ',' : '' }}
        </li>
      </ul>
    </footer>

    <CollectionsModal v-if="collectionsVisible" :entry="entry.id" @close="collectionsVisible = false" />
  </article>
</template>

<script>
import * as clipboard from 'clipboard-polyfill'
import FlexLink from '@/components/ui/FlexLink.vue'
import Tag from '@/components/ui/Tag.vue'
import Icon from '~/components/ui/Icon.vue'
import MiniPlayer from '~/components/audio/MiniPlayer.vue'
import CollectionsModal from '@/components/CollectionsModal.vue'

export default {
  name: 'Entry',
  components: { CollectionsModal, MiniPlayer, Icon, Tag, FlexLink },
  props: {
    entry: {
      type: Object,
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
    box: {
      type: Boolean,
      default: () => false
    },
    hideActions: {
      type: Boolean,
      default: () => false
    },
    hideSources: {
      type: Boolean,
      default: () => false
    }
  },
  data () {
    return {
      collectionsVisible: false
    }
  },
  computed: {
    anchor () {
      return `e${this.entry.id}`
    },
    highlighted () {
      return this.$route.hash === `#${this.anchor}`
    },
    inlineSources () {
      return this.entry.sources.filter(s => s.type !== 'url')
    },
    urlSources () {
      return this.entry.sources.filter(s => s.type === 'url')
    }
  },
  methods: {
    copyLines () {
      const clipboardBuffer = new clipboard.DT()

      clipboardBuffer.setData('text/plain', this.generateTextLines().join('\r\n'))

      clipboard.write(clipboardBuffer)

      this.$notify({ type: 'success', text: 'Entry copied to clipboard' })
    },
    generateTextLines () {
      const lines = []

      if (this.entry.suggestion) {
        lines.push('[Suggestion]', '')
      }

      this.$refs.lines.childNodes.forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          return
        }

        // eslint-disable-next-line unicorn/prefer-text-content
        lines.push(child.innerText)

        if (child.className === 'entry__line') {
          lines.push('')
        }
      })

      if (this.entry.footnote) {
        // eslint-disable-next-line unicorn/prefer-text-content
        lines.push(this.$refs.footnote.innerText, '')
      }

      const link = `${window.location.protocol}//${window.location.host}/`
      lines.push(link)

      return lines
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
    border-radius: 3px;
    border: 1px solid rgba(0, 76, 110, .5);
    box-shadow: 0 1px 0 rgba(0, 76, 110, .2);
  }

  &--highlighted {
    box-shadow: $theme-color 0 0 10px inset !important;
  }

  &--suggestion {
    background: $suggestion-entry-background;
  }

  &__anchor {
    position: absolute;
    top: -50px;
    visibility: hidden;
    display: block;
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

  &__suggestion-marker {
    display: block;
    margin-left: 16px;
    padding: 2px 8px;
    color: $text-light;
    background: darken($inserted-color, 20%);
    border-radius: 3px;

    &:hover, &:active, &:focus {
      color: $text-light;
      background: saturate(darken($inserted-color, 15%), 10%);
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

    p {
      margin-top: .7em;
      margin-bottom: .7em;
    }
  }

  &__footer {
    display: flex;
    flex-wrap: wrap;
  }

  &__footnote {
    width: 100%;
    margin-bottom: 8px;
  }

  &__tags {
    display: flex;
    align-items: flex-start;

    .tag {
      margin-right: 4px;

      &:last-child {
        margin-right: 0;
      }
    }
  }

  &__url-sources {
    display: flex;
    text-align: right;
    list-style-type: none;
    padding: 0 0 0 16px;
    margin-left: auto;
    overflow-x: hidden;
    justify-content: flex-end;
    flex: 1;

    li {
      display: inline-block;
      margin-right: 6px;

      &:last-child {
        margin-right: 0;
      }
    }

    li.entry__url-sources-item {
      display: flex;
      overflow: hidden;

      a {
        display: inline-block;
        text-overflow: ellipsis;
        overflow: hidden;
        white-space: nowrap;
        flex: 1;
      }
    }
  }

  &__url-source {
    vertical-align: bottom;
    color: $theme-color;
    border-bottom: 1px dotted $theme-color;
  }

  @media (max-width: $small-breakpoint) {
    &__footer {
      flex-direction: column;
      align-items: stretch;
    }

    &__tags {
      flex-wrap: wrap;
    }

    &__url-sources {
      max-width: 100%;
      padding: 8px 0 0;
    }
  }
}
</style>
