<template>
  <article class="entry-diff">
    <client-only>
      <TreeDiff :old="oldLines" :new="newLines" tag="div" class="entry-diff__content" />
    </client-only>
    <footer class="entry-diff__footer">
      <div class="entry-diff__tags">
        <Tag
          v-for="{ tag, inserted, deleted } in tagDiff"
          :tag="tag"
          :key="tag"
          :class="{ 'entry-diff__tag--inserted': inserted, 'entry-diff__tag--deleted': deleted }"
        />
      </div>
      <ul v-if="urlSourceDiff.length > 0" class="entry-diff__url-sources">
        <li>Sources:</li>
        <li v-for="({ source, inserted, deleted }, index) in urlSourceDiff" class="entry-diff__url-sources-item">
          <FlexLink
            :url="source.url"
            :class="['entry-diff__url-source', { 'entry-diff__url-source--inserted': inserted, 'entry-diff__url-source--deleted': deleted }]"
          >
            <span>{{ source.title }}</span>
          </FlexLink>{{ urlSourceDiff.length - 1 > index ? ',' : '' }}
        </li>
      </ul>
    </footer>
  </article>
</template>

<script>
import { Edits, LinearDiffer, TreeDiff } from 'vuesual-diff'
import Tag from '@/components/ui/Tag.vue'
import FlexLink from '@/components/ui/FlexLink.vue'

class TagDiffer extends LinearDiffer {
  isEqualChar (a, b) {
    return a === b
  }

  matchChar (char, regex) {
    return char.match(regex)
  }

  matchString (string, regex) {
    return false
  }
}

class UrlSourceDiffer extends LinearDiffer {
  isEqualChar (a, b) {
    if (a === b) {
      return true
    }

    if (a === undefined || b === undefined) {
      return false
    }

    if (a.title !== b.title) {
      return false
    }

    return a.url === b.url
  }

  matchChar (char, regex) {
    return char.title.match(regex)
  }

  matchString (string, regex) {
    return false
  }
}

export default {
  name: 'EntryDiff',
  components: { FlexLink, Tag, TreeDiff },
  props: {
    old: {
      type: Object,
      required: true
    },
    new: {
      type: Object,
      required: true
    }
  },
  computed: {
    oldLines () {
      return this.old.lines.flatMap(({ speaker, content }) => [
        `<h4 class="entry-diff__speaker">${speaker}</h4>`,
        `<div class="entry-diff__line">${content}</div>`
      ]).join('\n')
    },
    newLines () {
      return this.new.lines.flatMap(({ speaker, content }) => [
        `<h4 class="entry-diff__speaker">${speaker}</h4>`,
        `<div class="entry-diff__line">${content}</div>`
      ]).join('\n')
    },
    tagDiff () {
      if (this.old.tags.length === 0 && this.new.tags.length === 0) {
        return []
      }

      return new TagDiffer().diff(this.old.tags, this.new.tags)
        .flatMap(([action, tags]) => tags.map(tag => ({
          inserted: action === Edits.INSERT,
          deleted: action === Edits.DELETE,
          tag
        })))
    },
    urlSourceDiff () {
      const oldUrlSources = this.old.sources.filter(s => s.type === 'url')
      const newUrlSources = this.new.sources.filter(s => s.type === 'url')

      if (oldUrlSources.length === 0 && newUrlSources.length === 0) {
        return []
      }

      return new UrlSourceDiffer().diff(oldUrlSources, newUrlSources)
        .flatMap(([action, sources]) => sources.map(source => ({
          inserted: action === Edits.INSERT,
          deleted: action === Edits.DELETE,
          source
        })))
    }
  }
}
</script>

<style lang="scss">
.entry-diff {
  position: relative;
  display: flex;
  flex-direction: column;
  $inserted-color: #7fd7c4;
  $deleted-color: #e88e89;

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

  &__tag {
    &--inserted, &--deleted {
      color: rgba(0, 0, 0, 0.8);
    }

    &--inserted {
      background: darken(saturate($inserted-color, 15%), 15);
    }

    &--deleted {
      text-decoration: line-through;
      background: darken(saturate($deleted-color, 15%), 15);
    }
  }

  &__url-source {
    &--inserted {
      background: $inserted-color;
    }

    &--deleted {
      text-decoration: line-through;
      background: $deleted-color;
    }
  }

  &__content {
    padding-top: 8px;
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

    li.entry-diff__url-sources-item {
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

  ins.vuesual-diff__inserted, del.vuesual-diff__deleted {
    white-space: pre-wrap;
  }

  .vuesual-diff__inserted {
    text-decoration: inherit;
    background: $inserted-color !important;
  }

  .vuesual-diff__deleted {
    text-decoration: line-through;
    background: $deleted-color !important;
  }

  li.vuesual-diff__inserted {
    box-shadow: -40px 0 0 $inserted-color;
  }

  li.vuesual-diff__deleted {
    box-shadow: -40px 0 0 $deleted-color;
  }
}
</style>
