<template>
  <div class="grid-row">
    <slot />
  </div>
</template>

<script>
export default {
  name: 'GridRow'
}
</script>

<style lang="scss">
.grid-row {
  display: flex;
  flex-wrap: wrap;
}
</style>
