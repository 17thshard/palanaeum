<template>
  <Card class="list-card">
    <slot slot="header" name="header" />
    <slot slot="actions" name="actions" />
    <div v-if="$slots['list-header']" class="list-card__list-header">
      <slot name="list-header" />
    </div>
    <ul class="list-card__list">
      <slot />
    </ul>
    <div v-if="$slots['list-footer']" class="list-card__list-footer">
      <slot name="list-footer" />
    </div>
  </Card>
</template>

<script>
import Card from '@/components/ui/Card.vue'

export default {
  name: 'ListCard',
  components: { Card }
}
</script>

<style lang="scss">
.list-card {
  .card__content {
    padding: 0;
    border: none;

    & > *:last-child {
      border-bottom-left-radius: 3px;
      border-bottom-right-radius: 3px;
    }
  }

  &__list {
    padding: 0;
    list-style-type: none;
    border: 1px solid #ccc;

    & > li {
      border-bottom: 1px solid #ccc;

      &:last-child {
        border-bottom: none;
      }
    }
  }

  &__list-header, &__list-footer {
    padding: 8px 16px;
    background: $theme-color;
    color: $text-light;
  }
}
</style>
