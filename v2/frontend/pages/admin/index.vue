<template>
  <GridContainer class="admin">
    <GridCell :width="12">
      <PageTitle>Administration</PageTitle>
    </GridCell>
    <GridCell :width="12">
      <h3>Server space</h3>
      <meter class="admin__server-space" value="343825002496" min="0" max="946662244352" />
      <strong>320.21 Gb</strong> of <strong>881.65 Gb</strong> used (<strong>516.58 Gb</strong> free)
    </GridCell>
  </GridContainer>
</template>

<script>
import PageTitle from '@/components/layout/PageTitle.vue'
import GridContainer from '@/components/ui/GridContainer.vue'
import GridCell from '@/components/ui/GridCell.vue'

export default {
  components: { GridCell, GridContainer, PageTitle },
  head: {
    title: 'Administration'
  }
}
</script>

<style lang="scss">
.admin {
  h3 {
    margin-top: 0;
    margin-bottom: 8px;
    line-height: 1;
    font-size: 1.4rem;
  }

  &__server-space {
    display: block;
    width: 100%;
    height: 1.5rem;
    border: none;
    border-radius: 3px;
    overflow: hidden;
    background: darken($content-background, 5%);
    box-shadow: 0 0 0 1px #ddd;
    margin-bottom: 8px;

    &::-webkit-meter-bar {
      background: darken($content-background, 5%);
      border: none;
      border-radius: 3px;
    }

    &::-webkit-meter-optimum-value {
      background: $a-hover-color;
      border-radius: 3px;
    }

    &::-moz-meter-bar {
      background: $a-hover-color;
      border-radius: 3px;
    }
  }
}
</style>
