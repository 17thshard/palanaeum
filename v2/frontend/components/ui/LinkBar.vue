<template>
  <nav class="link-bar">
    <ul class="link-bar__links">
      <li v-for="link in links">
        <a v-if="!link.children" :title="link.title" :href="link.href" :target="link.target" class="link-bar__link">
          <span v-if="link.icon" :class="['fa', `fa-${link.icon}`]" aria-hidden="true" />
          {{ link.text }}
        </a>
        <DropdownLink v-else :link="link" class="link-bar__link" />
      </li>
    </ul>
  </nav>
</template>

<script>
import DropdownLink from '@/components/ui/DropdownLink.vue'

export default {
  name: 'LinkBar',
  components: { DropdownLink },
  props: {
    links: {
      type: Array,
      default: () => []
    }
  }
}
</script>

<style lang="scss">
.link-bar {
  font-family: 'Roboto Slab', serif;
  display: flex;
  align-items: stretch;

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
}
</style>
