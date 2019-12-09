<template>
  <form class="searchbar w3-hide-small w3-hide-medium" action="/adv_search/" method="get">
    <input
      type="search"
      class="searchbar__input"
      title="search"
      placeholder="Search..."
      name="query"
      value=""
    >
    <button class="w3-btn w3-round w3-theme-dark" type="submit">
      <span class="fa fa-search" aria-hidden="true" />
    </button>
  </form>
</template>

<script>
export default {
  name: 'SearchBar'
}
</script>

<style lang="scss">
.searchbar {
  display: flex;
  font-size: 13px;
  align-items: center;
  padding-left: 15px;
  padding-right: 4px;

  &__input {
    flex-grow: 1;
    margin-right: 16px;
  }
}
</style>
