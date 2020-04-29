<template>
  <div class="audio-editor">
    <PageTitle>Edit audio source</PageTitle>
    <nuxt-link to="/events/american-fork-high-school-signing" class="breadcrumb">
      <Icon name="arrow-left" />
      Back to event
    </nuxt-link>
    <div class="audio-editor__sticky-sentinel-wrapper">
      <div ref="stickySentinel" class="audio-editor__sticky-sentinel" />
    </div>
    <header :class="['audio-editor__header', { 'audio-editor__header--sticky': headerSticky }]">
      <div class="audio-editor__header-wrapper">
        <AudioPlayer
          ref="player"
          v-model="playerState"
          :snippets="snippets"
          :locked-snippet="lockedSnippet"
          @unlock="lockedSnippet = null"
          source="https://wob.coppermind.net/media/sources/415/The_Dusty_Wheel_Interview_TIyQE.mp3"
          key-controls
        >
          <input
            v-model="title"
            aria-label="Source title"
            type="text"
            class="audio-editor__title"
          >

          <Button theme="secondary">
            Rename
          </Button>
        </AudioPlayer>
        <div class="audio-editor__player-actions">
          <Button @click="addSnippet">
            <Icon name="plus" />
            Add snippet
          </Button>
          <Button @click="extendSnippet" :disabled="selectedSnippet === null">
            <Icon name="arrows-alt-h" />
            Extend snippet
          </Button>
          <Button :disabled="selectedSnippet === null" theme="delete">
            <Icon name="volume-mute" />
            Mute snippet
          </Button>
        </div>
        <div class="audio-editor__actions">
          <h2>Manage snippets</h2>
          <Button>
            <Icon name="save" />
            Save
          </Button>
        </div>
      </div>
    </header>
    <div class="audio-editor__snippets-wrapper">
      <table class="audio-editor__snippets">
        <thead>
          <tr>
            <th>ID</th>
            <th />
            <th>Start</th>
            <th>End</th>
            <th>Name</th>
            <th>Optional</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="{ snippet, index } in sortedSnippets"
            :key="snippet.id"
            :class="['audio-editor__snippet', { 'audio-editor__snippet--selected': selectedSnippet === index }]"
          >
            <td @click.self="toggleSelection(index)">
              {{ snippet.id }}
            </td>
            <td @click.self="toggleSelection(index)">
              <button @click="playSnippet(snippet)" class="circle-button" title="Play snippet">
                <Icon name="play" />
              </button>
            </td>
            <td @click.self="toggleSelection(index)">
              <div class="audio-editor__time-input">
                <Button @click="changeSnippetTime(snippet, 'start', -1)" title="Increase snippet start time by 1 second">
                  <Icon name="minus" />
                </Button>
                <input
                  :value="formatTime(snippet.startTime)"
                  @keyup.enter="$event.target.blur()"
                  @change="onSnippetTimeChange(snippet, 'start', $event)"
                  type="text"
                  aria-label="Snippet start time"
                >
                <Button @click="changeSnippetTime(snippet, 'start', 1)" title="Decrease snippet start time by 1 second">
                  <Icon name="plus" />
                </Button>
              </div>
            </td>
            <td @click.self="toggleSelection(index)">
              <div class="audio-editor__time-input">
                <Button @click="changeSnippetTime(snippet, 'end', -1)" title="Increase snippet end time by 1 second">
                  <Icon name="minus" />
                </Button>
                <input
                  :value="formatTime(snippet.endTime)"
                  @keyup.enter="$event.target.blur()"
                  @change="onSnippetTimeChange(snippet, 'end', $event)"
                  type="text"
                  aria-label="Snippet end time"
                >
                <Button @click="changeSnippetTime(snippet, 'end', 1)" title="Decrease snippet end time by 1 second">
                  <Icon name="plus" />
                </Button>
              </div>
            </td>
            <td @click.self="toggleSelection(index)" class="audio-editor__snippet-name">
              <input v-model="snippet.name" aria-label="Snippet name" type="text">
            </td>
            <td @click.self="toggleSelection(index)" class="audio-editor__snippet-optional">
              <input v-model="snippet.optional" aria-label="Snippet optional" type="checkbox">
            </td>
            <td @click.self="toggleSelection(index)" class="audio-editor__snippet-actions">
              <template v-if="!snippet.new">
                <nuxt-link v-if="snippet.entryExists" to="/entry/1/edit" class="audio-editor__snippet-action">
                  <Icon name="pencil-alt" />
                  Edit entry
                </nuxt-link>
                <nuxt-link v-else to="/entry/1/edit" class="audio-editor__snippet-action">
                  <Icon name="plus" />
                  Create entry
                </nuxt-link>
                <Button v-if="snippet.hidden" @click="snippet.hidden = false" class="audio-editor__snippet-action">
                  <Icon name="eye" />
                  Show
                </Button>
                <Button v-else @click="snippet.hidden = true" class="audio-editor__snippet-action">
                  <Icon name="eye-slash" />
                  Hide
                </Button>
              </template>
              <button @click="deleteSnippet(index)" class="audio-editor__snippet-action audio-editor__snippet-action--delete">
                <Icon name="trash-alt" type="regular" />
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import AudioPlayer from '@/components/audio/AudioPlayer.vue'
import Icon from '@/components/ui/Icon.vue'
import PageTitle from '@/components/layout/PageTitle.vue'
import Button from '@/components/ui/Button.vue'
import { hasOnlyModifiers, KEY_CODES } from '@/utils/keys'

const convertTimeToHHMMSS = (seconds, includeHour) => {
  const hhmmss = new Date(seconds * 1000).toISOString().substr(11, 8)

  return !includeHour ? hhmmss.substr(3) : hhmmss
}

export default {
  components: { Button, PageTitle, Icon, AudioPlayer },
  head: {
    title: 'Audio source'
  },
  data () {
    return {
      title: 'The_Dusty_Wheel_Interview_TIyQE.m4a',
      headerSticky: false,
      playerState: {
        current: 0,
        total: 0
      },
      snippets: [
        {
          id: 1,
          type: 'entry',
          startTime: 284,
          endTime: 494,
          name: 'RoW update',
          optional: false,
          hidden: true,
          entryExists: true
        },
        {
          id: 2,
          type: 'entry',
          startTime: 494,
          endTime: 544,
          name: 'favorite RoW scene',
          optional: false,
          hidden: false,
          entryExists: false
        }
      ],
      selectedSnippet: null,
      lockedSnippet: null
    }
  },
  computed: {
    sortedSnippets () {
      return this.snippets
        .map((snippet, index) => ({ snippet, index }))
        .sort((a, b) =>
          a.snippet.startTime === b.snippet.startTime ? a.snippet.endTime - b.snippet.endTime : a.snippet.startTime - b.snippet.startTime
        )
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

    window.addEventListener('keyup', this.onKeyPress)
  },
  destroyed () {
    window.removeEventListener('keyup', this.onKeyPress)
  },
  methods: {
    onKeyPress (event) {
      if (document.activeElement !== null && document.activeElement !== document.body) {
        return
      }

      switch (event.keyCode) {
        case KEY_CODES.SPACE:
          if (hasOnlyModifiers(event, ['shift'])) {
            this.extendSnippet()
          } else if (hasOnlyModifiers(event, [])) {
            this.addSnippet()
          }
          break
        case KEY_CODES.BACKSPACE:
        case KEY_CODES.DELETE:
          if (this.selectedSnippet !== null && hasOnlyModifiers(event, [])) {
            this.deleteSnippet(this.selectedSnippet)
          }
          break
      }
    },
    addSnippet () {
      const existing = this.snippets.findIndex(snippet => snippet.startTime === this.playerState.current)
      if (existing !== -1) {
        this.selectedSnippet = existing
        return
      }

      this.selectedSnippet = this.snippets.length
      this.snippets.push(
        {
          new: true,
          id: Math.max(...this.snippets.map(s => s.id)) + 1,
          type: 'entry',
          name: '',
          startTime: this.playerState.current,
          endTime: this.playerState.current + 10,
          optional: false,
          hidden: false,
          entryExists: false
        }
      )
    },
    extendSnippet () {
      if (this.selectedSnippet === null) {
        return
      }

      const selectedSnippet = this.snippets[this.selectedSnippet]
      selectedSnippet.endTime = this.playerState.current
      this.validateSnippetTimes(selectedSnippet)
    },
    deleteSnippet (index) {
      const snippet = this.snippets[index]
      if (this.selectedSnippet === index) {
        this.selectedSnippet = null
      }

      if (this.lockedSnippet === snippet) {
        this.lockedSnippet = null
      }

      this.snippets.splice(index, 1)
    },
    toggleSelection (index) {
      this.selectedSnippet = this.selectedSnippet === index ? null : index
    },
    playSnippet (snippet) {
      this.lockedSnippet = snippet
      this.$nextTick(() => {
        this.$refs.player.playLockedSnippet()
      })
    },
    formatTime (time) {
      return convertTimeToHHMMSS(time, this.playerState.total > 3600)
    },
    onSnippetTimeChange (snippet, field, event) {
      const text = event.target.value

      if (/^([0-9]+:){0,2}[0-9]+$/.test(text)) {
        const parts = text.split(':')
        snippet[`${field}Time`] = parts.reduce((acc, value, index) => acc + value * (60 ** (parts.length - index - 1)), 0)
      }

      this.validateSnippetTimes(snippet)

      event.target.value = this.formatTime(snippet[`${field}Time`])
    },
    changeSnippetTime (snippet, field, delta) {
      snippet[`${field}Time`] = snippet[`${field}Time`] + delta
      this.validateSnippetTimes(snippet)
    },
    validateSnippetTimes (snippet) {
      snippet.startTime = Math.max(0, Math.min(snippet.startTime, this.playerState.total))
      snippet.endTime = Math.max(0, Math.min(snippet.endTime, this.playerState.total))

      if (snippet.endTime <= snippet.startTime) {
        snippet.endTime = snippet.startTime + 10
      }
    }
  }
}
</script>

<style lang="scss">
.audio-editor {
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

      .audio-editor__header-wrapper {
        padding: 8px 16px 16px;
        box-shadow: 0 0 16px rgba(0, 0, 0, 0.5);
        border-bottom: #ccc 1px solid;
      }
    }
  }

  &__title {
    width: auto;
    margin-right: 8px;
  }

  &__player-actions {
    text-align: center;
    margin-top: 16px;
  }

  &__actions {
    display: flex;
    align-items: center;
    margin-top: 16px;

    h2 {
      margin-right: auto;
    }
  }

  &__snippets {
    width: 100%;
    border-collapse: collapse;
    border: 1px solid #ddd;

    &-wrapper {
      overflow-x: auto;
    }

    thead {
      background: $theme-color;
      color: $text-light;

      th {
        padding: 8px 10px;
        text-align: left;
      }
    }

    tbody tr {
      border-bottom: 1px solid #ddd;

      &:nth-child(even) {
        background-color: #f1f1f1;
      }
    }

    td {
      vertical-align: middle;
      padding: 8px 8px;
    }
  }

  &__snippet {
    &--selected td {
      background-color: #c8ebfb !important;
    }

    &-name {
      width: 60%;
      min-width: 150px;
    }

    &-optional {
      text-align: center;
    }

    &-actions {
      width: 30%;
      word-spacing: 5px;
      min-width: 100px;
    }

    &-action {
      cursor: pointer;
      text-decoration: none;
      background: none;
      border: none;
      appearance: none;
      color: inherit !important;;
      font-size: 1rem;
      padding: 0;
      margin: 0;
      font-weight: 400;
      word-spacing: normal;
      display: inline-block;
      border-radius: 0;

      &:hover, &:active, &:focus {
        background: none;
        color: $a-hover-color !important;
      }

      &:disabled {
        color: lighten($a-hover-color, 15%) !important;
        cursor: not-allowed;
      }

      &--delete {
        color: $error-color !important;

        &:hover, &:active, &:focus {
          color: darken($error-color, 15%) !important;
        }

        &:disabled {
          color: lighten($error-color, 15%) !important;
          cursor: not-allowed;
        }
      }
    }
  }

  &__time-input {
    display: flex;

    .button {
      padding: 4px 10px;
    }

    .button:first-child {
      border-bottom-right-radius: 0;
      border-top-right-radius: 0;
    }

    input {
      border-radius: 0;
      width: 5.5em;
      text-align: center;
    }

    .button:last-child {
      border-bottom-left-radius: 0;
      border-top-left-radius: 0;
    }

    &--invalid input {
      color: $error-color;
    }
  }

}
</style>
