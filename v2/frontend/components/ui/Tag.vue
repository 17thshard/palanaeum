<template>
  <a class="tag" href="#">
    {{ tag }}
  </a>
</template>

<script>
export default {
  name: 'Tag',
  props: {
    tag: {
      type: String,
      required: true
    }
  }
}
</script>

<style lang="scss">
.tag {
  display: inline-block;
  padding: 4px 8px;
  color: $text-light;
  background: $tag-background;
  font-size: 0.8rem;
  line-height: 1;

  &:before {
    content: '#';
    margin-right: -3px;
  }
}
</style>
