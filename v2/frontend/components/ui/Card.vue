<template>
  <div class="card">
    <header class="card__header">
      <h2>
        <slot name="header" />
      </h2>
    </header>
    <div class="card__content">
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
    padding: 8px 16px;

    h2 {
      display: block;
      margin: 0;
      font-family: roboto slab, serif;
      font-weight: 400;
      font-size: 22px;
    }
  }

  &__content {
    padding: 8px 16px;
    border: 1px solid #ccc;
    background: #fff;
    border-bottom-left-radius: 3px;
    border-bottom-right-radius: 3px;
  }
}
</style>
