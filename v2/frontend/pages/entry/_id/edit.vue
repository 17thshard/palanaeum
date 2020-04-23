<template>
  <div class="entry-editor">
    <div :class="['entry-editor__header', { 'entry-editor__header--sticky': scrollPosition > 160 }]">
      <div class="entry-editor__header-wrapper">
        <h2>Snippets assigned to this entry</h2>
        <AudioPlayer
          :source-id="8631"
          title="RoW update RoW update RoW update RoW update RoW update RoW update RoW update"
          source="https://wob.coppermind.net/media/snippets/477/284_210.mp3"
          title-editable
        />
        <h2>Create or modify an entry</h2>
      </div>
    </div>
    <TextEditor content="" />
    <div>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
      Lorem ipsum<br>
    </div>
  </div>
</template>

<script>
import AudioPlayer from '@/components/audio/AudioPlayer.vue'
import ScrollListener from '@/mixins/ScrollListener'
import TextEditor from '@/components/editor/TextEditor.vue'

export default {
  components: { TextEditor, AudioPlayer },
  mixins: [ScrollListener],
  head: {
    title: 'Edit entry'
  }
}
</script>

<style lang="scss">
.entry-editor {
  display: flex;
  flex-direction: column;

  &__header {
    position: sticky;

    &-wrapper {
      padding: 8px 0 16px;
    }

    &--sticky {
      width: calc(100% + 32px);
      max-width: $max-sticky-width;
      margin-left: -16px;
      padding-bottom: 16px;
      top: 47px;
      overflow: hidden;
      z-index: 1;

      @media (max-width: $medium-breakpoint) {
        top: 44px;
      }

      .entry-editor__header-wrapper {
        background: $content-background;
        padding: 8px 16px 16px;
        box-shadow: 0 0 16px rgba(0, 0, 0, 0.5);
        border-bottom: #ccc 1px solid;
      }
    }
  }
}
</style>
