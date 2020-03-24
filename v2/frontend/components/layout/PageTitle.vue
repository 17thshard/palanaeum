<template>
  <header class="page-title">
    <h1 class="page-title__heading">
      <slot />
    </h1>
    <div v-if="$slots.actions" class="page-title__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style lang="scss">
.page-title {
  display: flex;
  align-items: center;
  background-color: $header-color;
  color: $text-light;
  padding: 10px 16px;

  &__heading {
    display: block;
    margin: 0;
    font-family: roboto slab, serif;
    font-weight: 400;
    font-size: 24px;
  }

  &__actions {
    margin-left: auto;
  }
}
</style>
