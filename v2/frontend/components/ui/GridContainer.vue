<template>
  <div class="grid-container">
    <slot />
  </div>
</template>

<script>
export default {
  name: 'GridContainer'
}
</script>

<style lang="scss">
.grid-container {
  display: grid;
  $columns: null;
  @for $i from 1 through $grid-units {
    $columns: $columns minmax(0, #{1 / $grid-units}fr);
  }
  grid-template-columns: $columns;
  grid-gap: 16px;

  @media (max-width: $medium-breakpoint) {
    grid-template-columns: 100%;
  }
}
</style>
