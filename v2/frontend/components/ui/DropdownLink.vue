<template>
  <div class="dropdown-link">
    <a :title="link.title" @click.prevent="active = !active" href="#" class="dropdown-link__header">
      <span v-if="link.icon" :class="['fa', `fa-${link.icon}`]" aria-hidden="true" />
      {{ link.text }}
    </a>
    <ul :class="['dropdown-link__children', { 'dropdown-link__children--active': active }]">
      <li v-for="child in link.children">
        <a :title="child.title" :href="child.href" class="dropdown-link__child">
          <span v-if="child.icon" :class="['fa', `fa-${child.icon}`]" aria-hidden="true" />
          {{ child.text }}
        </a>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'DropdownLink',
  props: {
    link: {
      type: Object,
      required: true
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
      if (!this.$el.contains(event.target)) {
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

  &__header {
    padding: 8px 16px;
  }

  &__children {
    list-style-type: none;
    display: none;
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

    li {
      display: block;
    }

    &--active {
      display: flex;
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
}
</style>
