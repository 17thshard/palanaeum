<template>
  <Modal @close="$emit('close')">
    <template slot="header" v-if="type === 'insert'">
      Insert link
    </template>
    <template slot="header" v-else>
      Edit link
    </template>
    <form @submit.prevent="$emit('submit')" class="link-properties">
      <label for="link-properties__url">URL</label>
      <input id="link-properties__url" ref="url" :value="value.url" @input="onInput('url', $event)" type="text">
      <label for="link-properties__title">Title</label>
      <input id="link-properties__title" :value="value.title" @input="onInput('title', $event)" type="text">
      <label for="link-properties__target">Target</label>
      <select id="link-properties__target" :value="value.target" @input="onInput('target', $event)">
        <option value="">
          None
        </option>
        <option value="_blank">
          New window
        </option>
      </select>
      <div class="link-properties__buttons">
        <Button theme="secondary" type="submit">
          OK
        </Button>
        <Button @click="$emit('close')" type="button">
          Cancel
        </Button>
      </div>
    </form>
  </Modal>
</template>

<script>
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'

export default {
  name: 'LinkPropertiesModal',
  components: { Button, Modal },
  props: {
    type: {
      type: String,
      required: true
    },
    value: {
      type: Object,
      required: true
    }
  },
  mounted () {
    this.$refs.url.focus()
  },
  methods: {
    onInput (field, event) {
      this.$emit('input', { ...this.value, [field]: event.target.value })
    }
  }
}
</script>

<style lang="scss">
.link-properties {
  display: grid;
  align-items: center;
  grid-template-columns: auto 1fr;
  grid-gap: 8px;

  &__buttons {
    grid-column: 1/span 2;
  }
}
</style>
