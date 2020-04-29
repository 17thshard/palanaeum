<template>
  <li class="new-source">
    <div class="new-source__preview">
      <ImageSource
        v-if="type === 'image'"
        :thumbnail-width="50"
        :thumbnail-height="50"
        url="https://wob.coppermind.net/media/sources/115/Payden_McRoberts_Roshar_From_Space.png"
        thumbnail-url="https://wob.coppermind.net/media/cache/00/49/0049065f696c54e78fe7535a8a43eecc.png"
        description="Payden_McRoberts_Roshar_From_Space.png"
      />
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
import ImageSource from '@/components/ImageSource.vue'

export default {
  name: 'NewSource',
  components: { ImageSource, MiniPlayer },
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
