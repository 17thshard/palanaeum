<template>
  <div class="audio-editor">
    <PageTitle>Edit audio source</PageTitle>
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
        <div class="audio-editor__actions">
          <Button>
            <Icon name="plus" />
            Add snippet
          </Button>
          <Button>
            <Icon name="arrows-alt-h" />
            Extend snippet
          </Button>
        </div>
      </div>
    </header>
    <h2>Manage snippets</h2>
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
        <tr v-for="(snippet, index) in snippets" :key="snippet.id" class="audio-editor__snippet">
          <td>{{ snippet.id }}</td>
          <td>
            <button @click="playSnippet(snippet)" class="circle-button" title="Play snippet">
              <Icon name="play" />
            </button>
          </td>
          <td>
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
          <td>
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
          <td class="audio-editor__snippet-name">
            <input v-model="snippet.name" aria-label="Snippet name" type="text">
          </td>
          <td class="audio-editor__snippet-optional">
            <input v-model="snippet.optional" aria-label="Snippet optional" type="checkbox">
          </td>
          <td class="audio-editor__snippet-actions">
            <nuxt-link v-if="snippet.entryExists" to="/entry/1/edit" class="audio-editor__snippet-action">
              <Icon name="pencil-alt" />
              Edit entry
            </nuxt-link>
            <nuxt-link v-else to="/entry/1/edit" class="audio-editor__snippet-action">
              <Icon name="plus" />
              Create entry
            </nuxt-link>
            <Button class="audio-editor__snippet-action">
              <Icon name="eye-slash" />
              Hide
            </Button>
            <button @click="snippets.splice(index, 1)" class="audio-editor__snippet-action audio-editor__snippet-action--delete">
              <Icon name="trash-alt" type="regular" />
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import AudioPlayer from '@/components/audio/AudioPlayer.vue'
import Icon from '@/components/ui/Icon.vue'
import PageTitle from '@/components/layout/PageTitle.vue'
import Button from '@/components/ui/Button.vue'

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
          name: 'RoW update',
          optional: false,
          entryExists: true,
          startTime: 284,
          endTime: 494
        },
        {
          id: 2,
          type: 'entry',
          name: 'favorite RoW scene',
          optional: false,
          entryExists: false,
          startTime: 494,
          endTime: 544
        }
      ],
      lockedSnippet: null
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

      event.target.value = this.formatTime(snippet[`${field}Time`])
    },
    changeSnippetTime (snippet, field, delta) {
      const newValue = snippet[`${field}Time`] + delta
      if (newValue < 0 || newValue > this.playerState.total) {
        return
      }

      snippet[`${field}Time`] = newValue
    }
  }
}
</script>

<style lang="scss">
.audio-editor {
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

  &__actions {
    text-align: center;
    margin-top: 16px;
  }

  &__snippets {
    width: 100%;
    border-collapse: collapse;
    border: 1px solid #ddd;

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
    &-name {
      width: 60%;
    }

    &-optional {
      text-align: center;
    }

    &-actions {
      width: 30%;
      word-spacing: 5px;
    }

    &-action {
      cursor: pointer;
      text-decoration: none;
      background: none;
      border: none;
      -webkit-appearance: none;
      color: inherit;
      font-size: 1rem;
      padding: 0;
      margin: 0;
      font-weight: 400;
      word-spacing: normal;
      display: inline-block;

      &:hover, &:active, &:focus {
        background: none;
        color: $a-hover-color;
      }

      &:disabled {
        color: lighten($a-hover-color, 15%);
        cursor: not-allowed;
      }

      &--delete {
        color: $error-color;

        &:hover, &:active, &:focus {
          color: darken($error-color, 15%);
        }

        &:disabled {
          color: lighten($error-color, 15%);
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
