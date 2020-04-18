<template>
  <nav class="pagination">
    <nuxt-link
      :to="{ name: $route.name, query: { ...$route.query, page: 1 } }"
      :class="['button', { 'button--disabled': currentPage === 1 }]"
      aria-label="First"
    >
      <Icon name="angle-double-left" />
    </nuxt-link>
    <nuxt-link
      :to="{ name: $route.name, query: { ...$route.query, page: currentPage - 1 } }"
      :class="['button', { 'button--disabled': currentPage === 1 }]"
      aria-label="Previous"
    >
      <Icon name="angle-left" />
    </nuxt-link>

    <div
      :class="[
        'pagination__list-container',
        {
          'pagination__list-container--left-overflow': leftOverflowVisible,
          'pagination__list-container--right-overflow': rightOverflowVisible
        }
      ]"
    >
      <ul
        ref="list"
        :style="{ '--magnitude': Math.floor(Math.log10(totalPages)) }"
        @mousewheel="scrollHorizontally"
        @DOMMouseScroll="scrollHorizontally"
        @scroll="updateOverflow"
        class="pagination__list"
      >
        <li v-if="pages.length !== 0 && pages[0] !== 1" class="pagination__list-item">
          <Button @click="expanded = true">
            &hellip;
          </Button>
        </li>
        <li v-for="p in pages" :key="p" :data-page="p.toString()" class="pagination__list-item pagination__list-item-page">
          <nuxt-link
            :to="{ name: $route.name, query: { ...$route.query, page: p } }"
            :class="['button', { 'button--active': currentPage === p }]"
          >
            {{ p }}
          </nuxt-link>
        </li>
        <li v-if="pages.length !== 0 && pages[pages.length - 1] !== totalPages" class="pagination__list-item">
          <Button @click="expanded = true">
            &hellip;
          </Button>
        </li>
      </ul>
    </div>

    <nuxt-link
      :to="{ name: $route.name, query: { ...$route.query, page: currentPage + 1 } }"
      :class="['button', { 'button--disabled': currentPage === totalPages }]"
      aria-label="Next"
    >
      <Icon name="angle-right" />
    </nuxt-link>
    <nuxt-link
      :to="{ name: $route.name, query: { ...$route.query, page: totalPages } }"
      :class="['button', { 'button--disabled': currentPage === totalPages }]"
      aria-label="Last"
    >
      <Icon name="angle-double-right" />
    </nuxt-link>
  </nav>
</template>

<script>
import Icon from '@/components/ui/Icon.vue'
import Button from '@/components/ui/Button.vue'

const range = (start, endInclusive) => Array.from({ length: endInclusive - start + 1 }, (_, i) => start + i)

export default {
  name: 'Pagination',
  components: { Button, Icon },
  props: {
    totalPages: {
      type: Number,
      required: true
    }
  },
  data () {
    return {
      expanded: false,
      leftOverflowVisible: false,
      rightOverflowVisible: false
    }
  },
  computed: {
    currentPage () {
      return Number.parseInt(this.$route.query.page || '1', 10)
    },
    pages () {
      if (this.expanded) {
        return range(1, this.totalPages)
      }

      // Always display 9 pages
      // The current selection is supposed to be centered if possible
      // Hence, display the previous and next 4 pages when we haven't reached the end
      if (this.currentPage < this.totalPages - 5) {
        const start = Math.max(1, this.currentPage - 4)
        const end = Math.min(start + 8, this.totalPages)
        return range(start, end)
      } else {
        const start = Math.max(1, this.totalPages - 8)
        const end = this.totalPages
        return range(start, end)
      }
    }
  },
  watch: {
    currentPage () {
      this.$nextTick(() => {
        this.scrollToCurrentPage()
      })
    },
    expanded () {
      this.$nextTick(() => {
        this.updateOverflow()
        this.scrollToCurrentPage()
      })
    }
  },
  mounted () {
    window.addEventListener('resize', this.updateOverflow)
    this.updateOverflow()
    this.scrollToCurrentPage()
  },
  methods: {
    scrollToCurrentPage () {
      this.$refs.list.querySelector(`li[data-page='${this.currentPage}']`).scrollIntoView()
    },
    scrollHorizontally (event) {
      const e = window.event || event
      const delta = Math.max(-1, Math.min(1, e.wheelDelta || -e.detail))
      this.$refs.list.scrollLeft -= delta * 40
      e.preventDefault()
    },
    updateOverflow () {
      const { list } = this.$refs
      this.leftOverflowVisible = list.scrollLeft > 0
      this.rightOverflowVisible = list.scrollLeft + list.clientWidth < list.scrollWidth
    }
  }
}
</script>

<style lang="scss">
.pagination {
  display: flex;
  overflow: hidden;

  .button {
    border-radius: 0;
    flex-shrink: 0;
  }

  &__list {
    display: flex;
    list-style-type: none;
    padding: 0;
    margin: 0;
    overflow-y: hidden;
    overflow-x: auto;
    overscroll-behavior: contain;

    &-container {
      position: relative;
      overflow: hidden;
      height: 37px;

      &:before, &:after {
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        width: 16px;
        z-index: 1;
        pointer-events: none;
        transition: opacity 0.2s ease-in-out;
        opacity: 0;
      }

      &:before {
        left: 0;
        background: linear-gradient(90deg, rgba(0, 0, 0, 0.2) 0, rgba(0, 0, 0, 0) 100%);
      }

      &:after {
        right: 0;
        background: linear-gradient(-90deg, rgba(0, 0, 0, 0.2) 0, rgba(0, 0, 0, 0) 100%);
      }

      &--left-overflow:before {
        opacity: 1;
      }

      &--right-overflow:after {
        opacity: 1;
      }
    }

    &-item-page .button {
      box-sizing: content-box;
      min-width: calc((var(--magnitude) + 1) * 0.7em);
    }
  }
}
</style>
