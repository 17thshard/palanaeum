<template>
  <nav :class="['link-bar', { 'link-bar--vertical': vertical }]">
    <ul :class="['link-bar__links', { 'link-bar__links--vertical': vertical }]">
      <li v-for="(link, index) in links" :key="index">
        <DropdownLink
          v-if="link.children"
          :link="{ ...link, icon: displayIcons ? link.icon : undefined }"
          :vertical="vertical"
          :inline-children="inlineDropdowns"
          class="link-bar__link"
        />
        <a
          v-else
          :href="link.url"
          :title="link.title"
          :target="link.target"
          class="link-bar__link"
        >
          <span v-if="displayIcons && link.icon" :class="['fa', `fa-${link.icon}`]" aria-hidden="true">
            <RoundBadge v-if="link.badge !== undefined" type="icon">{{ link.badge }}</RoundBadge>
          </span>
          {{ link.text }}
          <RoundBadge v-if="(!displayIcons || link.icon === undefined) && link.badge !== undefined" class="dropdown-link__badge">
            {{ link.badge }}
          </RoundBadge>
        </a>
      </li>
    </ul>
  </nav>
</template>

<script>
import DropdownLink from '@/components/ui/DropdownLink.vue'
import RoundBadge from '@/components/ui/RoundBadge.vue'

export default {
  name: 'LinkBar',
  components: { RoundBadge, DropdownLink },
  props: {
    links: {
      type: Array,
      default: () => []
    },
    vertical: {
      type: Boolean,
      default: () => false
    },
    inlineDropdowns: {
      type: Boolean,
      default: () => false
    },
    displayIcons: {
      type: Boolean,
      default: () => true
    }
  }
}
</script>

<style lang="scss">
.link-bar {
  font-family: 'Roboto Slab', serif;
  display: flex;
  align-items: stretch;

  &--vertical {
    flex-direction: column;
  }

  &__links {
    list-style-type: none;
    display: flex;
    align-items: stretch;
    margin: 0;
    padding: 0;

    li {
      display: flex;
      align-items: stretch;
    }

    &--vertical {
      flex-direction: column;

      li {
        flex-direction: column;
      }
    }
  }

  &__link {
    display: flex;
    align-items: center;
    padding: 8px 16px;

    .fa {
      margin-right: 4px;
    }

    &:hover {
      color: $text-light;
      background: $theme-color;
    }
  }

  &__badge {
    margin-left: 4px;
  }
}
</style>
