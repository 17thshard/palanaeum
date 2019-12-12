<template>
  <div class="dropdown-link">
    <a :title="link.title" @click.prevent="active = !active" href="#" class="dropdown-link__header">
      <span v-if="link.icon" :class="['fa', `fa-${link.icon}`]" aria-hidden="true" />
      {{ link.text }}
    </a>
    <ul v-if="active || inlineChildren" :class="['dropdown-link__children', { 'dropdown-link__children--inline': vertical }]">
      <li v-for="child in link.children">
        <a
          v-if="child.action"
          @click.prevent="child.action()"
          :title="child.title"
          :target="child.target"
          href="#"
          class="dropdown-link__child"
        >
          <span v-if="child.icon" :class="['fa', `fa-${child.icon}`]" aria-hidden="true" />
          {{ child.text }}
        </a>
        <FlexLink
          v-else
          :url="child.url"
          :title="child.title"
          :target="child.target"
          class="dropdown-link__child"
        >
          <span v-if="child.icon" :class="['fa', `fa-${child.icon}`]" aria-hidden="true" />
          {{ child.text }}
        </FlexLink>
      </li>
    </ul>
  </div>
</template>

<script>
import FlexLink from '@/components/ui/FlexLink.vue'

export default {
  name: 'DropdownLink',
  components: { FlexLink },
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
  data () {
    return {
      active: false
    }
  },
  mounted () {
    document.addEventListener('click', this.handleOutsideClick)
  },
  destroyed () {
    document.removeEventListener('click', this.handleOutsideClick)
  },
  methods: {
    handleOutsideClick (event) {
      if (!this.vertical && !this.$el.contains(event.target)) {
        this.active = false
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
    right: 0;
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

  .dropdown-link__children--inline .dropdown-link__child {
    &:hover {
      color: $a-hover-color;
      background: none;
    }
  }
}
</style>
