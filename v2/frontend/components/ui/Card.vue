<template>
  <div class="card w3-card">
    <header class="w3-container card__header">
      <h2>
        <slot name="header" />
      </h2>
    </header>
    <div class="block w3-border w3-padding">
      <slot />
    </div>
  </div>
</template>

<script>
export default {
  name: 'Card'
}
</script>

<style lang="scss">
.card {
  box-shadow: none;

  &__header {
    background-color: $header-color;
    color: $text-light;

    h2 {
      display: block;
      margin: 10px 0;
      font-family: roboto slab, serif;
      font-weight: 400;
      font-size: 22px;
    }
  }
}
</style>
