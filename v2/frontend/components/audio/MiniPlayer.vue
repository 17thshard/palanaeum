<template>
  <div class="mini-player">
    <template v-if="url !== undefined">
      <audio ref="audio" :src="url" preload="none" />
      <button @click="toggle" class="circle-button" title="Play/Pause">
        <Icon :name="playing ? 'pause' : 'play'" fixed-width />
      </button>
    </template>
    <Icon v-else name="gears" fixed-width class="circle-button" title="Snippet is being prepared" />
  </div>
</template>

<script>
import { mapState, mapMutations } from 'vuex'
import Icon from '~/components/ui/Icon.vue'

let uuid = 0

export default {
  name: 'MiniPlayer',
  components: { Icon },
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
  mounted () {
    this.$refs.audio.addEventListener('ended', () => {
      if (this.playing) {
        this.playing = false
        this.releaseLock()
        this.$refs.audio.currentTime = 0
      }
    })
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
