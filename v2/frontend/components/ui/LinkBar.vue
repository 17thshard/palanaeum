<template>
  <nav :class="['link-bar', { 'link-bar--vertical': vertical }]">
    <ul :class="['link-bar__links', { 'link-bar__links--vertical': vertical }]">
      <li v-for="link in links">
        <DropdownLink
          v-if="link.children"
          :link="{ ...link, icon: displayIcons ? link.icon : undefined }"
          :vertical="vertical"
          :inline-children="inlineDropdowns"
          class="link-bar__link"
        />
        <a
          v-else-if="link.action"
          @click.prevent="link.action()"
          :title="link.title"
          :target="link.target"
          href="#"
          class="link-bar__link"
        >
          <Icon
            v-if="displayIcons && link.icon"
            v-bind="link.icon instanceof Object ? { fixedWidth: true, ...link.icon } : { name: link.icon, fixedWidth: true }"
          >
            <Badge v-if="link.text === undefined && link.badge !== undefined" usage="icon">
              {{ link.badge }}
            </Badge>
          </Icon>
          {{ link.text }}
          <Badge v-if="link.text !== undefined && link.badge !== undefined" class="link-bar__badge">
            {{ link.badge }}
          </Badge>
        </a>
        <FlexLink
          v-else
          :url="link.url"
          :title="link.title"
          :target="link.target"
          class="link-bar__link"
        >
          <Icon
            v-if="displayIcons && link.icon"
            v-bind="link.icon instanceof Object ? { fixedWidth: true, ...link.icon } : { name: link.icon, fixedWidth: true }"
          >
            <Badge v-if="link.text === undefined && link.badge !== undefined" usage="icon">
              {{ link.badge }}
            </Badge>
          </Icon>
          {{ link.text }}
          <Badge v-if="link.text !== undefined && link.badge !== undefined" class="link-bar__badge">
            {{ link.badge }}
          </Badge>
        </FlexLink>
      </li>
    </ul>
  </nav>
</template>

<script>
import DropdownLink from '@/components/ui/DropdownLink.vue'
import FlexLink from '@/components/ui/FlexLink.vue'
import Badge from '@/components/ui/Badge.vue'
import Icon from '~/components/ui/Icon.vue'

export default {
  name: 'LinkBar',
  components: { Icon, Badge, FlexLink, DropdownLink },
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

    .icon {
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
