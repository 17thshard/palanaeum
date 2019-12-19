<template>
  <div class="mini-player">
    <template v-if="url !== undefined">
      <audio ref="audio" :src="url" preload="none" />
      <button :class="['mini-player__button fa fa-fw', playing ? 'fa-pause' : 'fa-play']" @click="toggle" title="Play/Pause" />
    </template>
    <span v-else class="mini-player__button fa fa-fw fa-gears" title="Snippet is being prepared" />
  </div>
</template>

<script>
import { mapState, mapMutations } from 'vuex'

let uuid = 0

export default {
  name: 'MiniPlayer',
  props: {
    url: {
      type: String,
      default: () => undefined
    }
  },
  data () {
    return {
      playing: false
    }
  },
  computed: mapState(['miniPlayerLock']),
  watch: {
    miniPlayerLock (newHolder) {
      if (newHolder !== this.uuid) {
        this.pause()
      }
    }
  },
  beforeCreate () {
    this.uuid = uuid.toString()
    uuid += 1
  },
  methods: {
    toggle () {
      if (this.playing) {
        this.pause()
        this.releaseLock()
      } else {
        this.play()
        this.acquireLock(this.uuid)
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
    ...mapMutations({
      acquireLock: 'acquireMiniPlayerLock',
      releaseLock: 'releaseMiniPlayerLock'
    })
  }
}
</script>

<style lang="scss">
.mini-player {
  &__button {
    font-size: 1.5em;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2em;
    margin: 0 7px;
    padding: .5em;
    cursor: pointer;
    color: $text-light;
    border-width: 0;
    border-radius: 50%;
    background: $button1-background;

    &:hover, &:focus {
      background: $button1-hover;
    }
  }
}
</style>
