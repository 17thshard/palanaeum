<template>
  <div class="audio-player">
    <div v-if="$slots.default" class="audio-player__header">
      <slot />
    </div>
    <div @click="scrub" @mousemove="updateScrubIndicator" class="audio-player__track">
      <div
        v-for="section in bufferedSections"
        :key="`buffered-${section.startTime}`"
        :style="calculateSnippetStyle(section)"
        class="audio-player__buffered"
      />
      <div :style="{ width: `${(currentTime / totalTime * 100).toFixed(3)}%` }" class="audio-player__progress" />
      <div
        v-for="snippet in snippets"
        :key="snippet.id"
        :class="[
          'audio-player__snippet',
          `audio-player__snippet--${snippet.type}`,
          { 'audio-player__snippet--locked': snippet === lockedSnippet }
        ]"
        :style="calculateSnippetStyle(snippet)"
      />
      <template v-if="lockedSnippet !== null">
        <div v-if="leftLockIndicatorStyles !== null" :style="leftLockIndicatorStyles" class="audio-player__lock-indicator" />
        <div v-if="rightLockIndicatorStyles !== null" :style="rightLockIndicatorStyles" class="audio-player__lock-indicator" />
      </template>
      <div
        :class="['audio-player__scrub-indicator', { 'audio-player__scrub-indicator--right': scrubPosition > 0.5 }]"
        :style="{ left: `${(scrubPosition * 100).toFixed(3)}%` }"
      >
        <span class="audio-player__scrub-indicator-content">{{ scrubTimestamp }}</span>
      </div>
    </div>
    <div class="audio-player__controls">
      <div class="audio-player__buttons">
        <Button @click="move(-60)" :disabled="!loaded" :title="addKeyLabel('-60s', 'D')" class="audio-player__control">
          <Icon name="fast-backward" fixed-width />
        </Button>
        <Button @click="move(-5)" :disabled="!loaded" :title="addKeyLabel('-5s', 'F')" class="audio-player__control">
          <Icon name="step-backward" fixed-width />
        </Button>
        <Button :disabled="!loaded" @click="toggle" :title="addKeyLabel(playing ? 'Pause' : 'Play', 'G')" class="audio-player__control">
          <Icon :name="playing ? 'pause' : 'play'" fixed-width />
        </Button>
        <Button @click="move(5)" :disabled="!loaded" :title="addKeyLabel('+5s', 'H')" class="audio-player__control">
          <Icon name="step-forward" fixed-width />
        </Button>
        <Button @click="move(60)" :disabled="!loaded" :title="addKeyLabel('+60s', 'J')" class="audio-player__control">
          <Icon name="fast-forward" fixed-width />
        </Button>
        <div class="audio-player__timestamp">
          {{ timestamp }} / {{ duration }}
        </div>
      </div>
      <Button v-if="lockedSnippet !== null" @click="$emit('unlock')" class="audio-player__control audio-player__unlock">
        <Icon name="lock" />
        Locked to snippet. Click to unlock
      </Button>
      <div class="audio-player__playback-rate">
        <label for="audio-player__playback-rate">Playback speed</label>
        <select id="audio-player__playback-rate" v-model="playbackRate">
          <option v-for="rate in [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]" :key="rate" :value="rate">
            {{ rate }}x
          </option>
        </select>
      </div>
    </div>
    <audio
      ref="audio"
      @loadeddata="onAudioLoaded"
      @timeupdate="onTimeUpdate"
      @ended="onAudioEnded"
      @progress="onAudioProgress"
      preload="auto"
      class="audio-player__audio"
    />
  </div>
</template>

<script>
import Icon from '@/components/ui/Icon.vue'
import Button from '@/components/ui/Button.vue'
import { hasOnlyModifiers } from '@/utils/keys'

const convertTimeToHHMMSS = (seconds, includeHour) => {
  const hhmmss = new Date(seconds * 1000).toISOString().substr(11, 8)

  return !includeHour ? hhmmss.substr(3) : hhmmss
}

const KEY_CODES = {
  FAST_BACKWARD: 68, // D
  STEP_BACKWARD: 70, // F
  TOGGLE: 71, // G
  STEP_FORWARD: 72, // H
  FAST_FORWARD: 74 // J
}

export default {
  name: 'AudioPlayer',
  components: { Button, Icon },
  props: {
    source: {
      type: String,
      required: true
    },
    snippets: {
      type: Array,
      default: () => []
    },
    lockedSnippet: {
      type: Object,
      default: () => null
    },
    keyControls: {
      type: Boolean,
      default: () => false
    }
  },
  data () {
    return {
      loaded: false,
      playing: false,
      currentTime: this.lockedSnippet !== null ? this.lockedSnippet.startTime : 0,
      totalTime: 0,
      playbackRate: 1.0,
      scrubPosition: 0,
      bufferedSections: []
    }
  },
  computed: {
    timestamp () {
      return convertTimeToHHMMSS(this.currentTime, this.totalTime >= 3600)
    },
    duration () {
      return convertTimeToHHMMSS(this.totalTime, this.totalTime >= 3600)
    },
    scrubTimestamp () {
      return convertTimeToHHMMSS(this.totalTime * this.scrubPosition, this.totalTime >= 3600)
    },
    leftLockIndicatorStyles () {
      if (this.lockedSnippet === null || this.lockedSnippet.startTime === 0) {
        return null
      }

      return this.calculateSnippetStyle({ startTime: 0, endTime: this.lockedSnippet.startTime })
    },
    rightLockIndicatorStyles () {
      if (this.lockedSnippet === null || this.lockedSnippet.endTime === this.totalTime) {
        return null
      }

      return this.calculateSnippetStyle({ startTime: this.lockedSnippet.endTime, endTime: this.totalTime })
    }
  },
  watch: {
    playbackRate (newValue) {
      if (!this.$refs.audio) {
        return
      }

      this.$refs.audio.playbackRate = this.$refs.audio.defaultPlaybackRate * newValue
    },
    currentTime (newValue) {
      this.$emit('input', { current: newValue, total: this.totalTime })
    },
    totalTime (newValue) {
      this.$emit('input', { current: this.currentTime, total: newValue })
    }
  },
  mounted () {
    this.$refs.audio.src = this.source
    window.addEventListener('keyup', this.onKeyPress)
  },
  destroyed () {
    window.removeEventListener('keyup', this.onKeyPress)
  },
  methods: {
    toggle () {
      if (this.playing) {
        this.pause()
      } else {
        this.play()
      }
    },
    play () {
      this.playing = true
      this.$refs.audio.play()
    },
    pause () {
      this.playing = false
      this.$refs.audio.pause()
    },
    move (seconds) {
      this.$refs.audio.currentTime += seconds
      this.clampToLock()
    },
    scrub () {
      this.$refs.audio.currentTime = this.scrubPosition * this.totalTime
      this.clampToLock()
    },
    updateScrubIndicator (event) {
      this.scrubPosition = event.offsetX / event.target.clientWidth
    },
    onAudioLoaded () {
      if (!this.$refs.audio || !this.$refs.audio.readyState >= 2) {
        return
      }

      this.$refs.audio.currentTime = this.currentTime
      this.totalTime = this.$refs.audio.duration
      this.loaded = true
    },
    clampToLock () {
      if (!this.$refs.audio || this.lockedSnippet === null) {
        return
      }

      if (this.$refs.audio.currentTime < this.lockedSnippet.startTime) {
        this.$refs.audio.currentTime = this.lockedSnippet.startTime
      }

      if (this.$refs.audio.currentTime > this.lockedSnippet.endTime) {
        this.$refs.audio.currentTime = this.lockedSnippet.endTime
      }
    },
    onTimeUpdate () {
      if (!this.$refs.audio) {
        return
      }

      this.currentTime = this.$refs.audio.currentTime

      if (this.lockedSnippet === null) {
        return
      }

      if (this.currentTime > this.lockedSnippet.endTime) {
        this.$refs.audio.currentTime = this.lockedSnippet.startTime
        this.pause()
      }
    },
    onAudioEnded () {
      if (this.playing) {
        this.playing = false
        this.$refs.audio.currentTime = 0
      }
    },
    onAudioProgress () {
      if (!this.$refs.audio) {
        return
      }

      const { buffered } = this.$refs.audio
      this.bufferedSections = []
      for (let i = 0; i < buffered.length; i++) {
        this.bufferedSections.push({ startTime: buffered.start(i), endTime: buffered.end(i) })
      }
    },
    calculateSnippetStyle ({ startTime, endTime }) {
      return {
        left: `${(startTime / this.totalTime * 100).toFixed(3)}%`,
        width: `${((endTime - startTime) / this.totalTime * 100).toFixed(3)}%`
      }
    },
    playLockedSnippet () {
      if (!this.$refs.audio || this.lockedSnippet === null) {
        return
      }

      this.$refs.audio.currentTime = this.lockedSnippet.startTime
      this.play()
    },
    onKeyPress (event) {
      if (!this.keyControls || (document.activeElement !== null && document.activeElement !== document.body) || !hasOnlyModifiers(event, [])) {
        return
      }

      switch (event.keyCode) {
        case KEY_CODES.FAST_BACKWARD:
          this.move(-60)
          break
        case KEY_CODES.STEP_BACKWARD:
          this.move(-5)
          break
        case KEY_CODES.TOGGLE:
          this.toggle()
          break
        case KEY_CODES.STEP_FORWARD:
          this.move(5)
          break
        case KEY_CODES.FAST_FORWARD:
          this.move(60)
          break
      }
    },
    addKeyLabel (text, key) {
      if (this.keyControls) {
        return `${text} (${key})`
      }

      return text
    }
  }
}
</script>

<style lang="scss">
.audio-player {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  border: 1px solid #ccc;
  border-radius: 5px;
  overflow: hidden;
  background: $content-background;

  &__header {
    display: flex;
    align-items: center;
    padding: 8px 16px;
    background: $theme-color;
    color: $text-light;
    overflow-x: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__track {
    position: relative;
    height: 1.5em;
    cursor: pointer;

    & > * {
      pointer-events: none;
    }
  }

  &__progress {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    background: $button2-hover;
  }

  &__buffered {
    position: absolute;
    top: 0;
    bottom: 0;
    background: #ccc;
  }

  &__snippet {
    position: absolute;
    top: 0;
    bottom: 0;
    opacity: 0.8;
    box-sizing: border-box;

    &--entry {
      background: $button1-hover;
      border-color: $button1-hover;
    }

    &--muted {
      background: #de3c1b;
      border-color: #de3c1b;
    }

    &--locked {
      background: none;
      border-width: 2px;
      border-style: solid;
      opacity: 1;
    }
  }

  &__scrub-indicator {
    display: none;
    align-items: center;
    position: absolute;
    top: 0;
    bottom: 0;
    box-sizing: border-box;
    border: 1px solid $theme-color;
    font-size: 0.9em;
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.8), 1px 0 0 rgba(255, 255, 255, 0.8), 0 -1px 0 rgba(255, 255, 255, 0.8), -1px 0 0 rgba(255, 255, 255, 0.8);

    &-content {
      position: absolute;
      left: 5px;
    }

    &--right .audio-player__scrub-indicator-content {
      left: auto;
      right: 5px;
    }
  }

  &__track:hover .audio-player__scrub-indicator {
    display: flex;
  }

  &__lock-indicator {
    position: absolute;
    top: 0;
    bottom: 0;
    background: lightgrey;
    opacity: 0.8;
  }

  &__controls {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    background: $theme-color;
    color: $text-light;

    @media (max-width: $medium-breakpoint) {
      flex-direction: column;
      align-items: stretch;
    }
  }

  &__buttons {
    display: flex;
    align-items: center;
  }

  &__control {
    border-radius: 0;
    align-self: stretch;
  }

  &__timestamp {
    font-size: 0.9em;
    margin-left: 8px;
    font-variant-numeric: tabular-nums;

    @media (max-width: $medium-breakpoint) {
      display: grid;
      text-align: right;
      flex: 1;
      padding-right: 16px;
    }
  }

  &__unlock {
    margin-left: 8px;
    padding-left: 8px;
    padding-right: 8px;
    font-size: 0.9em;

    .icon {
      font-size: 1.111em;
      margin-right: 3px;
    }

    @media (max-width: $medium-breakpoint) {
      margin-left: 0;
    }
  }

  &__playback-rate {
    display: flex;
    align-items: center;
    margin-left: auto;
    font-size: 0.9em;
    margin-right: 16px;

    label {
      display: block;
      margin-right: 4px;
      white-space: nowrap;
    }

    @media (max-width: $medium-breakpoint) {
      display: none;
    }
  }

  &__audio {
    display: none;
  }
}
</style>
