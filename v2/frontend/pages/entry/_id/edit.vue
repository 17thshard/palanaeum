<template>
  <div class="entry-editor">
    <PageTitle>Edit entry</PageTitle>
    <div class="entry-editor__sticky-sentinel-wrapper">
      <div ref="stickySentinel" class="entry-editor__sticky-sentinel" />
    </div>
    <div :class="['entry-editor__header', { 'entry-editor__header--sticky': headerSticky }]">
      <div class="entry-editor__header-wrapper">
        <h2>Snippets assigned to this entry</h2>
        <AudioPlayer
          :source-id="8631"
          title="RoW update"
          source="https://wob.coppermind.net/media/snippets/477/284_210.mp3"
        />
        <div class="entry-editor__actions">
          <h2>Create or modify an entry</h2>
          <Button>
            Save
          </Button>
        </div>
      </div>
    </div>
    <draggable
      v-model="lines"
      :animation="200"
      @start="drag = true"
      @end="drag = false"
      tag="section"
      class="entry-editor__lines"
      group="lines"
      ghost-class="entry-editor__line-ghost"
      handle=".entry-editor__line-drag-handle"
    >
      <transition-group :name="!drag ? 'flip-list' : null" tag="div" type="transition">
        <div v-for="(line, index) in lines" :key="line.order" class="entry-editor__line">
          <label :for="`entry-editor__line-speaker--${index}`" class="entry-editor__line-label">Speaker</label>
          <input :id="`entry-editor__line-speaker--${index}`" v-model="line.speaker" type="text">
          <div class="entry-editor__line-label entry-editor__line-content-label">
            <label>Line</label>
            <button :disabled="lines.length === 1" @click="lines.splice(index, 1)" class="entry-editor__delete">
              <Icon name="trash-alt" type="regular" />
              Delete
            </button>
          </div>
          <TextEditor v-model="line.content" />
          <div class="entry-editor__line-drag-handle" />
        </div>
      </transition-group>
    </draggable>
    <Button @click="addLine" theme="secondary" class="entry-editor__add-line">
      <Icon name="plus" />
      Add line
    </Button>
    <div class="entry-editor__form">
      <div class="entry-editor__form-label entry-editor__form-label--large">
        <label>Footnote</label>
      </div>
      <div class="entry-editor__form-control">
        <TextEditor v-model="footnote" />
      </div>
      <div class="entry-editor__form-label">
        <label>Tags</label>
      </div>
      <div class="entry-editor__form-control">
        <client-only>
          <vue-tags-input
            v-model="currentTag"
            :tags="tags"
            @tags-changed="newTags => tags = newTags"
          />
        </client-only>
      </div>
      <div class="entry-editor__form-label">
        <label>Metadata</label>
      </div>
      <div class="entry-editor__form-control entry-editor__metadata">
        <label for="entry-editor__date">Date</label>
        <input id="entry-editor__date" v-model="date" type="date">
        <input id="entry-editor__direct-submission" v-model="directSubmission" type="checkbox">
        <label for="entry-editor__direct-submission">Direct submission</label>
        <label :style="{ visibility: directSubmission ? 'visible' : 'hidden' }" for="entry-editor__reporter">reported by</label>
        <input id="entry-editor__reporter" v-model="reporter" :style="{ visibility: directSubmission ? 'visible' : 'hidden' }" type="text">
        <input id="entry-editor__paraphrased" v-model="paraphrased" type="checkbox">
        <label for="entry-editor__paraphrased">Paraphrased</label>
      </div>
    </div>
    <ListCard>
      <template slot="header">
        URL sources
      </template>
      <table class="entry-editor__url-sources">
        <thead>
          <tr>
            <th>Address</th>
            <th>Name</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(source, index) in urlSources" :key="source.order">
            <td><input v-model="source.url" aria-label="URL source address" type="url"></td>
            <td><input v-model="source.name" aria-label="URL source name" type="text"></td>
            <td>
              <button @click="urlSources.splice(index, 1)" class="entry-editor__delete">
                <Icon name="trash-alt" type="regular" />
                Delete
              </button>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="3">
              <Button @click="addUrlSource" class="entry-editor__url-sources-add">
                Add source
              </Button>
            </td>
          </tr>
        </tfoot>
      </table>
    </ListCard>
  </div>
</template>

<script>
import Draggable from 'vuedraggable'
import AudioPlayer from '@/components/audio/AudioPlayer.vue'
import TextEditor from '@/components/editor/TextEditor.vue'
import Icon from '@/components/ui/Icon.vue'
import PageTitle from '@/components/layout/PageTitle.vue'
import Button from '@/components/ui/Button.vue'
import ListCard from '@/components/ui/ListCard.vue'

export default {
  components: { ListCard, Button, PageTitle, Icon, TextEditor, AudioPlayer, Draggable },
  head: {
    title: 'Edit entry'
  },
  data () {
    return {
      drag: false,
      headerSticky: false,
      lines: [{ speaker: '', content: '', order: 0 }, { speaker: '', content: '', order: 1 }],
      footnote: '',
      currentTag: '',
      tags: [],
      date: '2020-04-02',
      directSubmission: false,
      reporter: '',
      paraphrased: false,
      urlSources: [{ url: 'https://www.youtube.com/watch?v=rl3SxTPZauQ', name: 'The Dusty Wheel Livestream 2020-04-01', order: 0 }]
    }
  },
  mounted () {
    const observer = new IntersectionObserver((records) => {
      for (const record of records) {
        const targetInfo = record.boundingClientRect
        this.headerSticky = targetInfo.bottom < 0
      }
    }, { threshold: [0] })
    observer.observe(this.$refs.stickySentinel)
  },
  methods: {
    addLine () {
      const order = Math.max(...this.lines.map(line => line.order)) + 1
      this.lines.push({ speaker: '', content: '', order })
    },
    addUrlSource () {
      const order = Math.max(...this.urlSources.map(source => source.order)) + 1
      this.urlSources.push({ url: '', name: '', order })
    }
  }
}
</script>

<style lang="scss">
.entry-editor {
  display: flex;
  flex-direction: column;

  &__sticky-sentinel {
    position: absolute;
    left: 0;
    right: 0;
    visibility: hidden;
    height: 11px;
    top: -60px;

    @media (max-width: $medium-breakpoint) {
      height: 14px;
    }

    &-wrapper {
      position: relative;
    }
  }

  &__header {
    position: sticky;
    top: 47px;

    @media (max-width: $medium-breakpoint) {
      top: 44px;
    }

    &-wrapper {
      padding: 8px 0 16px;
      background: $content-background;
    }

    &--sticky {
      width: calc(100% + 32px);
      max-width: $max-sticky-width;
      margin-left: -16px;
      padding-bottom: 16px;
      overflow: hidden;
      z-index: 1;

      .entry-editor__header-wrapper {
        padding: 8px 16px 16px;
        box-shadow: 0 0 16px rgba(0, 0, 0, 0.5);
        border-bottom: #ccc 1px solid;
      }
    }
  }

  &__actions {
    display: flex;
    align-items: center;
    margin-top: 16px;

    h2 {
      margin-right: auto;
    }
  }

  &__line {
    display: grid;
    padding: 8px 8px 8px 16px;
    grid-template-columns: 65px minmax(0, 1fr) 16px;
    grid-gap: 8px;
    border: 1px solid #ccc;
    border-left-width: 2px;
    border-bottom: none;

    &:nth-child(odd) {
      border-left-color: $theme-color;
    }

    &:nth-child(even) {
      background: #f1f1f1;
    }

    &:last-child {
      border-bottom: 1px solid #ccc;
    }

    &-move {
      transition: transform 0.5s;
    }

    &-no-move {
      transition: transform 0s;
    }

    &-ghost {
      opacity: 0.5;
      background: #c8ebfb !important;
    }

    &-drag-handle {
      grid-column: 3;
      grid-row: 1/span 2;
      width: 16px;
      cursor: pointer;
      background-repeat: no-repeat;
      background-position: 50%;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Cpath fill='%23B3C6CE' d='M7 2a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 2m0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 8m0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 7 14m6-8a2 2 0 1 0-.001-4.001A2 2 0 0 0 13 6m0 2a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 8m0 6a2 2 0 1 0 .001 4.001A2 2 0 0 0 13 14'/%3E%3C/svg%3E");
    }

    &-label {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      margin-top: 5px;
      font-weight: bold;
      margin-right: 8px;
    }

    &-content-label {
      margin-top: 8px;
    }

    .entry-editor__delete {
      margin-top: 8px !important;
    }
  }

  &__delete {
    cursor: pointer;
    text-decoration: none;
    color: $error-color;
    background: none;
    border: none;
    -webkit-appearance: none;
    font-size: 1rem;
    padding: 0;
    margin: 0;
    font-weight: 400;

    &:hover, &:active, &:focus {
      color: darken($error-color, 15%);
    }

    &:disabled {
      color: lighten($error-color, 15%);
      cursor: not-allowed;
    }
  }

  &__add-line {
    align-self: flex-end;
    margin: 8px 0;
  }

  &__form {
    display: grid;
    grid-template-columns: 81px minmax(0, 1fr);
    border: 1px solid #ccc;
    border-bottom: none;
    margin-bottom: 16px;

    &-label, &-control {
      border-bottom: 1px solid #ccc;

      &:nth-child(4n), &:nth-child(4n+3) {
        background: #f1f1f1;
      }
    }

    label {
      display: block;
      margin-top: 5px;
    }

    &-label {
      font-weight: bold;
      padding: 8px 0 8px 16px;

      &--large label {
        margin-top: 8px;
      }
    }

    &-control {
      padding: 8px;
    }
  }

  &__metadata {
    display: grid;
    align-items: flex-start;
    grid-template-columns: auto auto auto auto auto auto auto auto minmax(0, 1fr);
    grid-gap: 8px;
    grid-auto-flow: column;
    grid-auto-columns: auto;

    input[type="checkbox"] {
      margin-left: 8px;
      margin-top: 8px;
    }
  }

  &__url-sources {
    width: 100%;
    border-collapse: collapse;

    thead {
      background: $theme-color;
      color: $text-light;

      th {
        padding: 8px 10px;
        text-align: left;
      }
    }

    td {
      vertical-align: middle;
      padding: 4px 8px;
      width: 50%;

      &:last-child {
        width: auto;
        white-space: nowrap;
      }
    }

    tbody tr:first-child td {
      padding-top: 8px;
    }

    &-add {
      width: 100%;
      display: block;
      margin-bottom: 4px;
    }
  }
}
</style>
