<template>
  <form class="search-bar" action="/adv_search/" method="get">
    <input
      type="search"
      class="search-bar__input"
      title="search"
      placeholder="Search..."
      name="query"
      value=""
    >
    <Button theme="dark" type="submit"><span class="fa fa-search" aria-hidden="true" /></Button>
  </form>
</template>

<script>
import Button from '@/components/ui/Button.vue'
export default {
  name: 'SearchBar',
  components: { Button }
}
</script>

<style lang="scss">
.search-bar {
  display: flex;
  font-size: 13px;
  align-items: center;
  padding-left: 16px;
  padding-right: 4px;

  &__input {
    flex-grow: 1;
    margin-right: 16px;
  }
}
</style>
