<template>
  <div :class="['dropdown-link', { 'dropdown-link--vertical': vertical }]">
    <a ref="header" :title="link.title" @click.prevent="toggle" href="#" class="dropdown-link__header">
      <Icon
        v-if="link.icon"
        v-bind="link.icon instanceof Object ? { fixedWidth: true, ...link.icon } : { name: link.icon, fixedWidth: true }"
      >
        <Badge v-if="link.text === undefined && link.badge !== undefined && !vertical" usage="icon">{{ link.badge }}</Badge>
      </Icon>
      {{ link.text }}
      <Badge v-if="link.text !== undefined && link.badge !== undefined" class="dropdown-link__badge">
        {{ link.badge }}
      </Badge>
    </a>
    <ul
      ref="children"
      v-if="active || inlineChildren"
      :class="['dropdown-link__children', `dropdown-link__children--${alignment}`, { 'dropdown-link__children--inline': vertical }]"
    >
      <li v-for="child in link.children">
        <a
          v-if="child.action"
          @click.prevent="child.action()"
          :title="child.title"
          :target="child.target"
          href="#"
          class="dropdown-link__child"
        >
          <Icon
            v-if="child.icon"
            v-bind="child.icon instanceof Object ? { fixedWidth: true, ...child.icon } : { name: child.icon, fixedWidth: true }"
          />
          {{ child.text }}
          <Badge v-if="child.badge !== undefined" class="dropdown-link__badge">
            {{ child.badge }}
          </Badge>
        </a>
        <FlexLink
          v-else
          :url="child.url"
          :title="child.title"
          :target="child.target"
          class="dropdown-link__child"
        >
          <Icon
            v-if="child.icon"
            v-bind="child.icon instanceof Object ? { fixedWidth: true, ...child.icon } : { name: child.icon, fixedWidth: true }"
          />
          {{ child.text }}
          <Badge v-if="child.badge !== undefined" class="dropdown-link__badge">
            {{ child.badge }}
          </Badge>
        </FlexLink>
      </li>
    </ul>
  </div>
</template>

<script>
import FlexLink from '@/components/ui/FlexLink.vue'
import Badge from '@/components/ui/Badge.vue'
import Icon from '~/components/ui/Icon.vue'

export default {
  name: 'DropdownLink',
  components: { Icon, Badge, FlexLink },
  props: {
    link: {
      type: Object,
      required: true
    },
    vertical: {
      type: Boolean,
      default: () => false
    },
    inlineChildren: {
      type: Boolean,
      default: () => false
    }
  },
  inject: {
    dropdownBounds: {
      default () {
        return () => undefined
      }
    }
  },
  data () {
    return {
      active: false,
      alignment: 'left'
    }
  },
  mounted () {
    document.addEventListener('click', this.handleOutsideClick)
  },
  destroyed () {
    document.removeEventListener('click', this.handleOutsideClick)
  },
  methods: {
    toggle () {
      if (this.active) {
        this.close()
      } else {
        this.open()
      }
    },
    open () {
      this.active = true
      this.$nextTick(() => {
        let bounds = this.dropdownBounds()
        if (bounds === undefined) {
          bounds = new DOMRect(0, 0, window.innerWidth, window.innerHeight)
        }
        const right = this.$refs.header.getBoundingClientRect().left + this.$refs.children.getBoundingClientRect().width
        this.alignment = right > bounds.right ? 'right' : 'left'
      })
    },
    close () {
      this.active = false
    },
    handleOutsideClick (event) {
      if (!this.vertical && !this.$el.contains(event.target)) {
        this.close()
      }
    }
  }
}
</script>

<style lang="scss">
.dropdown-link {
  position: relative;
  padding: 0 !important;

  &--vertical {
    display: flex;
    flex-direction: column;
    align-items: stretch !important;
  }

  &__header {
    display: flex;
    align-items: center;
    padding: 8px 16px;

    .icon {
      margin-right: 4px;
    }

    &:hover {
      color: $text-light;
    }
  }

  &__children {
    list-style-type: none;
    display: flex;
    align-items: stretch;
    flex-direction: column;
    margin: 0;
    padding: 0;
    position: absolute;
    top: 100%;
    z-index: 1;
    min-width: 200px;
    border-radius: 3px 0 3px 3px;
    border: 1px solid #ccc;
    background: $entry-background;
    color: $text-dark;
    font-size: 1rem;

    &--inline {
      position: relative;
      border: none;
      border-radius: 0;

      .dropdown-link__child {
        &:hover {
          color: $a-hover-color;
          background: none;
        }
      }
    }

    &--left {
      left: 0;
    }

    &--right {
      right: 0;
    }

    li {
      display: block;
    }
  }

  &__child {
    display: flex;
    align-items: center;
    padding: 8px 16px;
    width: 100%;

    .icon {
      margin-right: 4px;
    }

    &:hover {
      color: $text-light;
      background: $theme-color;
    }
  }

  &__badge {
    font-size: 0.8em;
    margin-left: 4px;
  }

  &__header .dropdown-link__badge {
    font-size: 0.5em;
  }
}
</style>
