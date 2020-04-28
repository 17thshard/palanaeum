<template>
  <Modal @close="$emit('close')" class="collections-modal">
    <template slot="header">
      Manage collections for entry
    </template>
    <ul class="collections-modal__list">
      <li v-for="(collection, index) in collections" :key="index" class="collections-modal__list-item">
        <input :id="`collections-modal__list-item-${index}`" v-model="collection.active" type="checkbox">
        <label :for="`collections-modal__list-item-${index}`">{{ collection.name }} ({{ collection.count }})</label>
        <Icon :name="collection.type === 'private' ? 'lock' : 'globe-europe'" fixed-width />
      </li>
    </ul>
    <transition name="fade" mode="out-in">
      <Button
        v-if="!creating"
        @click="creating = true"
        class="collections-modal__create"
        theme="secondary"
        type="submit"
        title="Create"
      >
        <Icon name="plus" />
        Create collection
      </Button>
      <form v-else @submit.prevent="createCollection" class="collections-modal__create">
        <input type="text" aria-label="Collection name" autofocus>
        <Button theme="secondary" type="submit" title="Create">
          <Icon name="plus" />
        </Button>
      </form>
    </transition>
  </Modal>
</template>

<script>
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Icon from '@/components/ui/Icon.vue'

export default {
  name: 'CollectionsModal',
  components: { Icon, Button, Modal },
  props: {
    entry: {
      type: String,
      required: true
    }
  },
  data () {
    return {
      collections: [
        {
          active: false,
          name: 'test',
          count: 2,
          type: 'private'
        },
        {
          active: true,
          name: 'Wisdom Shard',
          count: 3,
          type: 'public'
        }
      ],
      creating: false,
      collectionName: ''
    }
  },
  methods: {
    createCollection () {
      this.creating = false
    }
  }
}
</script>

<style lang="scss">
.collections-modal {
  --fade-speed: 0.1s;

  .modal__window {
    min-width: 400px;
  }

  &__list {
    padding: 0;
    margin: 0;
    list-style-type: none;
    min-height: 6rem;
    overflow-y: auto;
    flex: 1;

    &-item {
      display: flex;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid #ddd;

      &:last-child {
        border-bottom: none;
      }

      input, .icon {
        flex-shrink: 0;
      }

      input {
        width: 1.5rem;
        height: 1.5rem;
        margin: 0;
      }

      label {
        flex: 1;
        margin: 0 8px;
        cursor: pointer;
      }

      .icon {
        color: rgba($text-dark, 0.5);
      }
    }
  }

  &__create {
    margin-top: 16px;
    width: 100%;
    flex-shrink: 0;
  }

  form.collections-modal__create {
    display: flex;

    input {
      margin-right: 8px;
    }

    .button {
      flex-shrink: 0;
    }
  }
}
</style>
