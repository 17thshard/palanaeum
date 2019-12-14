<template>
  <div class="dropdown-link">
    <a ref="header" :title="link.title" @click.prevent="toggle" href="#" class="dropdown-link__header">
      <span v-if="link.icon" :class="['fa', `fa-${link.icon}`]" aria-hidden="true">
        <Badge v-if="link.badge !== undefined && !vertical" usage="icon">{{ link.badge }}</Badge>
      </span>
      {{ link.text }}
      <Badge v-if="link.icon === undefined && link.badge !== undefined" class="dropdown-link__badge">
        {{ link.badge }}
      </Badge>
    </a>
    <ul
      ref="children"
      v-if="active || inlineChildren"
      :class="['dropdown-link__children', `dropdown-link__children--${alignment}`, { 'dropdown-link__children--inline': vertical }]"
    >
      <li v-for="(child, index) in link.children" :key="index">
        <a
          :href="child.url"
          :title="child.title"
          :target="child.target"
          class="dropdown-link__child"
        >
          <span v-if="child.icon" :class="['fa', `fa-${child.icon}`]" aria-hidden="true" />
          {{ child.text }}
          <Badge v-if="child.badge !== undefined" class="dropdown-link__badge">
            {{ child.badge }}
          </Badge>
        </a>
      </li>
    </ul>
  </div>
</template>

<script>
import Badge from '@/components/ui/Badge.vue'

export default {
  name: 'DropdownLink',
  components: { Badge },
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
  display: block !important;

  .fa {
    position: relative;
  }

  &__header {
    padding: 8px 16px;
    display: block;

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
