<template>
  <div
    ref="container"
    :style="{ width: `${thumbnailWidth}px` }"
    class="image-source"
  >
    <div :style="{ paddingBottom: `${((thumbnailHeight / thumbnailWidth) * 100).toFixed(3)}%` }" class="image-source__content">
      <a :href="url" @click.prevent="overlay = true" class="image-source__thumbnail">
        <img
          ref="image"
          v-show="!loading && !error"
          :src="visible ? thumbnailUrl : undefined"
          :alt="description"
        >
      </a>
      <LoadingSpinner v-if="loading" class="image-source__loading" />
      <img
        v-if="error"
        src="https://discordapp.com/assets/e0c782560fd96acd7f01fda1f8c6ff24.svg"
        alt="Could not load image"
        class="image-source__error"
      >
    </div>

    <CoolLightBox :items="[{ src: url, title: description }]" :index="overlay ? 0 : null" @close="overlay = false" />
  </div>
</template>

<script>
import CoolLightBox from 'vue-cool-lightbox'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import 'vue-cool-lightbox/dist/vue-cool-lightbox.min.css'

export default {
  name: 'ImageSource',
  components: { LoadingSpinner, CoolLightBox },
  props: {
    url: {
      type: String,
      required: true
    },
    thumbnailUrl: {
      type: String,
      required: true
    },
    description: {
      type: String,
      required: true
    },
    thumbnailWidth: {
      type: Number,
      required: true
    },
    thumbnailHeight: {
      type: Number,
      required: true
    }
  },
  data () {
    return {
      visible: false,
      loading: true,
      error: false,
      intersectionObserver: null,
      overlay: false
    }
  },
  watch: {
    src () {
      this.error = false
      this.loading = true
    }
  },
  mounted () {
    this.intersectionObserver = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          this.visible = true
        }
      },
      {
        threshold: 0.25
      }
    )
    this.intersectionObserver.observe(this.$refs.container)
    this.$refs.image.addEventListener('load', () => {
      this.loading = false
      this.error = false
    })
    this.$refs.image.addEventListener('error', () => {
      this.loading = false
      this.error = true
    })
  }
}
</script>

<style lang="scss">
.image-source {
  position: relative;
  display: flex;
  align-items: stretch;
  justify-content: stretch;
  background-color: rgba(0, 0, 0, .05);
  max-width: 100%;

  &__content {
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    width: 100%;
  }

  &__thumbnail {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    display: block;

    img {
      display: block;
    }
  }

  &__loading {
    position: absolute !important;
    top: 50%;
    margin-top: -0.5em;
    font-size: 2em;
  }
}
</style>
