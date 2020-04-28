<template functional>
  <header class="page-title">
    <h1 class="page-title__heading">
      <slot />
    </h1>
    <div v-if="$slots.actions" class="page-title__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script>
export default {
  name: 'PageTitle'
}
</script>

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
    display: grid;
    grid-auto-flow: column;
    grid-auto-columns: auto;
    grid-gap: 8px;
    align-items: center;
    margin-left: auto;
  }

  &__icon-link {
    font-size: 1.25em;
    margin: 0 8px;
  }

  @media (max-width: $small-breakpoint) {
    flex-direction: column;
    align-items: flex-start;

    &__actions {
      margin-left: 0;
    }
  }
}
</style>
