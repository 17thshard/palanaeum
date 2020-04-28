<template>
  <li class="new-source">
    <div class="new-source__preview">
      <img v-if="type === 'image'" src="https://wob.coppermind.net/media/cache/d1/6c/d16c9e32948efd553b9e7668e34d595e.jpg" alt="source">
      <MiniPlayer v-else url="https://wob.coppermind.net/media/sources/383/Take_Me_Away_interview_Rzkmu.mp3" />
    </div>
    <div class="new-source__description">
      <a href="#" class="new-source__name">{{ name }}</a>
      <a class="new-source__event">in {{ event }}</a>
    </div>
  </li>
</template>

<script>
import MiniPlayer from '@/components/audio/MiniPlayer.vue'

export default {
  name: 'NewSource',
  components: { MiniPlayer },
  props: {
    name: {
      type: String,
      required: true
    },
    event: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: () => 'image'
    }
  }
}
</script>

<style lang="scss">
.new-source {
  display: grid;
  grid-template-columns: 4em 1fr;
  align-items: center;
  padding: 8px 16px;

  &__preview {
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      max-width: 100%;
    }
  }

  &__description {
    margin-left: 7px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  &__name {
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
  }

  &__event {
    color: #757575;
    font-size: 0.8em;
  }
}
</style>
