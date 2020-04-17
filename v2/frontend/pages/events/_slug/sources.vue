<template>
  <ul class="event-sources">
    <li class="event-sources__entry">
      <div class="event-sources__entry-preview">
        <img src="https://wob.coppermind.net/media/cache/a3/f8/a3f8c702b509abd73aaffe2d1398fcd9.jpg">
      </div>
      <span class="event-sources__entry-uploader">Uploaded by: Podman36</span>
      <span class="event-sources__entry-name">CBE35F41-4C0D-4446-826C-FDD4752C8902.jpeg</span>
      <ul class="event-sources__entry-actions">
        <li>
          <a href="#">
            <Icon name="edit" />
            Edit entry
          </a>
        </li>
        <li>
          <a href="#">
            <Icon name="tag" />
            Rename
          </a>
        </li>
      </ul>
    </li>
    <li class="event-sources__entry">
      <div class="event-sources__entry-preview">
        <MiniPlayer url="https://wob.coppermind.net/media/sources/383/Take_Me_Away_interview_Rzkmu.mp3" />
      </div>
      <span class="event-sources__entry-uploader">Uploaded by: Pagerunner</span>
      <span class="event-sources__entry-name">The_Dusty_Wheel_Interview_TIyQE.m4a</span>
      <ul class="event-sources__entry-actions">
        <li>
          <a href="#">
            <Icon name="pencil-alt" />
            Edit
          </a>
        </li>
        <li class="event-sources__entry-snippet-count">
          12 snippets
        </li>
      </ul>
    </li>
    <li class="event-sources__entry">
      <div class="event-sources__entry-preview">
        <a
          href="https://www.17thshard.com/forum/topic/87900-american-fork-high-school-signing/?do=findComment&comment=945297"
          class="circle-button"
        >
          <Icon name="link" fixed-width />
        </a>
      </div>
      <a
        href="https://www.17thshard.com/forum/topic/87900-american-fork-high-school-signing/?do=findComment&comment=945297"
        class="event-sources__entry-name"
      >Blackout8444's report</a>
    </li>
  </ul>
</template>

<script>
import MiniPlayer from '@/components/audio/MiniPlayer.vue'
import Icon from '@/components/ui/Icon.vue'

export default {
  components: { Icon, MiniPlayer }
}
</script>

<style lang="scss">
.event-sources {
  list-style-type: none;
  padding-left: 0;
  margin: 0;

  &__entry {
    display: grid;
    grid-template-columns: 4em 1fr;
    grid-template-rows: 1fr auto 1fr;
    align-items: center;
    padding: 8px;
    border: 1px solid #ccc;
    border-bottom-width: 0;
    line-height: 1;
    grid-gap: 3px;

    &:first-child {
      border-top-left-radius: 3px;
      border-top-right-radius: 3px;
    }

    &:last-child {
      border-bottom-width: 1px;
      border-bottom-left-radius: 3px;
      border-bottom-right-radius: 3px;
    }

    &-preview {
      display: flex;
      align-items: center;
      justify-content: center;
      grid-row: 1/span 3;

      img {
        max-width: 100%;
      }
    }

    &-uploader {
      opacity: .6;
      text-align: right;
      align-self: flex-start;
    }

    &-name {
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
      grid-row: 2;
    }

    &-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      list-style-type: none;
      padding: 0;
      margin: 0;
      align-self: flex-end;

      li {
        margin-right: 8px;

        &:last-child {
          margin-right: 0;
        }
      }

      a {
        opacity: .6;
      }
    }

    &-snippet-count {
      background: $number-background;
      color: $text-light;
      padding: 4px 8px;
    }
  }
}
</style>
