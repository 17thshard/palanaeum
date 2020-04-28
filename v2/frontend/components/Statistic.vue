<template>
  <li class="statistic">
    <span class="statistic__value">{{ value }}</span>
    <span class="statistic__label">{{ value === 1 ? singular : plural }}</span>
  </li>
</template>

<script>
export default {
  name: 'Statistic',
  props: {
    value: {
      type: Number,
      required: true
    },
    singular: {
      type: String,
      required: true
    },
    plural: {
      type: String,
      required: true
    }
  }
}
</script>

<style lang="scss">
.statistic {
  display: block;
  text-align: center;
  padding: 8px 16px;

  &__value {
    font-size: 1.3em;
  }
}
</style>
