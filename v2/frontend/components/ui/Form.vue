<template>
  <form @submit.prevent="$emit('submit', event)" class="form">
    <slot />
  </form>
</template>

<script>
export default {
  name: 'Form'
}
</script>

<style lang="scss">
.form {
  display: grid;
  grid-gap: 8px 16px;
  grid-template-columns: minmax(auto, 100px) minmax(0, 1fr);

  &__instructions {
    grid-column: 1/span 2;

    p {
      margin: 8px 0;

      &:first-child {
        margin-top: 0;
      }

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  &__label {
    padding-top: 5px;
    font-weight: bold;
    text-align: right;
    grid-column: 1;
  }

  &__control {
    grid-column: 2;
  }

  div.form__control {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
  }

  &__help {
    margin-top: 4px;
    width: 100%;
    font-size: 0.9em;
    color: rgba($text-dark, 0.5);
  }

  ul.form__help {
    padding-left: 20px;
  }

  &__actions {
    display: flex;
    align-items: center;
    grid-column: 1/span 2;
  }

  &__buttons {
    margin-left: auto;
  }
}
</style>
