<template>
  <div class="text-editor">
    <client-only>
      <editor-menu-bar :editor="editor" v-slot="{ commands, isActive, getMarkAttrs }">
        <div class="text-editor__menu">
          <Button
            :disabled="editor.view.state.history$.done.eventCount"
            @click="commands.undo"
            class="text-editor__menu-button"
            title="Undo"
          >
            <Icon name="undo" fixed-width />
          </Button>

          <Button
            :disabled="editor.view.state.history$.undone.eventCount"
            @click="commands.redo"
            class="text-editor__menu-button"
            title="Redo"
          >
            <Icon name="redo" fixed-width />
          </Button>

          <div class="text-editor__menu-separator" />

          <Button
            :disabled="!isActive.link() && editor.selection.from === editor.selection.to"
            :class="['text-editor__menu-button', { 'text-editor__menu-button--active': isActive.link() }]"
            @click="openLinkModal(isActive.link() ? 'edit' : 'insert', getMarkAttrs('link'))"
            :title="isActive.link() ? 'Update Link' : 'Add Link'"
          >
            <Icon name="link" fixed-width />
          </Button>

          <Button
            :disabled="!isActive.link()"
            @click="commands.link({ href: null })"
            class="text-editor__menu-button"
            title="Remove link"
          >
            <Icon name="unlink" fixed-width />
          </Button>

          <div class="text-editor__menu-separator" />

          <Button
            :class="['text-editor__menu-button', { 'text-editor__menu-button--active': isActive.bold() }]"
            @click="commands.bold"
            title="Bold"
          >
            <Icon name="bold" fixed-width />
          </Button>

          <Button
            :class="['text-editor__menu-button', { 'text-editor__menu-button--active': isActive.italic() }]"
            @click="commands.italic"
            title="Italic"
          >
            <Icon name="italic" fixed-width />
          </Button>

          <Button
            :class="['text-editor__menu-button', { 'text-editor__menu-button--active': isActive.strike() }]"
            @click="commands.strike"
            title="Strikethrough"
          >
            <Icon name="strikethrough" fixed-width />
          </Button>

          <Button
            :class="['text-editor__menu-button', { 'text-editor__menu-button--active': isActive.underline() }]"
            @click="commands.underline"
            title="Underline"
          >
            <Icon name="underline" fixed-width />
          </Button>

          <Button
            :class="['text-editor__menu-button', { 'text-editor__menu-button--active': isActive.superscript() }]"
            @click="commands.superscript"
            title="Superscript"
          >
            <Icon name="superscript" fixed-width />
          </Button>

          <Button
            :class="['text-editor__menu-button', { 'text-editor__menu-button--active': isActive.subscript() }]"
            @click="commands.subscript"
            title="Subscript"
          >
            <Icon name="subscript" fixed-width />
          </Button>

          <div class="text-editor__menu-separator" />

          <Button
            @click="commands.clearFormatting"
            class="text-editor__menu-button"
            title="Clear formatting"
          >
            <Icon name="remove-format" fixed-width />
          </Button>

          <Button
            :class="['text-editor__menu-button', { 'text-editor__menu-button--active': showFindAndReplace }]"
            @click="showFindAndReplace = !showFindAndReplace"
            title="Find and replace"
          >
            <Icon name="search" fixed-width />
          </Button>

          <div v-if="showFindAndReplace" class="text-editor__find-and-replace">
            <div class="text-editor__find-and-replace-row">
              <input
                @input="executeCommand(findAndReplace.find(searchTerm))"
                v-model="searchTerm"
                type="text"
                class="text-editor__search-term"
                aria-label="Find..."
                placeholder="Find..."
              >
              <Button :disabled="searchTerm === ''" @click="executeCommand(findAndReplace.prevResult(searchTerm))" theme="secondary">
                Prev
              </Button>

              <Button :disabled="searchTerm === ''" @click="executeCommand(findAndReplace.nextResult(searchTerm))" theme="secondary">
                Next
              </Button>
            </div>

            <div class="text-editor__find-and-replace-row">
              <input
                :id="`text-editor__find-and-replace-match-case--${discriminator}`"
                v-model="findAndReplace.options.caseSensitive"
                type="checkbox"
              >
              <label :for="`text-editor__find-and-replace-match-case--${discriminator}`">Match case</label>

              <input
                :id="`text-editor__find-and-replace-whole-words--${discriminator}`"
                v-model="findAndReplace.options.wholeWords"
                type="checkbox"
              >
              <label :for="`text-editor__find-and-replace-whole-words--${discriminator}`">Whole words</label>
            </div>

            <div class="text-editor__find-and-replace-row">
              <input
                @keydown.enter.prevent="executeCommand(findAndReplace.replace(replacement))"
                v-model="replacement"
                type="text"
                class="text-editor__replacement"
                aria-label="Replace with..."
                placeholder="Replace with..."
              >
              <Button @click="executeCommand(findAndReplace.replace(replacement))" theme="secondary">
                Replace
              </Button>

              <Button @click="executeCommand(findAndReplace.replaceAll(replacement))" theme="secondary">
                Replace all
              </Button>
            </div>
          </div>
        </div>
      </editor-menu-bar>

      <editor-content :editor="editor" class="text-editor__content" />
      <LinkPropertiesModal
        v-if="showLinkModal"
        :type="linkType"
        v-model="linkProperties"
        @submit="applyLink"
        @close="showLinkModal = false"
      />
    </client-only>
  </div>
</template>

<script>
import { Editor, EditorContent, EditorMenuBar } from 'tiptap'
import { Blockquote, Bold, BulletList, HardBreak, History, Italic, ListItem, OrderedList, Strike, Underline } from 'tiptap-extensions'
import Icon from '@/components/ui/Icon.vue'
import Button from '@/components/ui/Button.vue'
import LinkPropertiesModal from '@/components/editor/LinkPropertiesModal.vue'
import Link from '@/components/editor/LinkMark'
import Superscript from '@/components/editor/SuperscriptMark'
import Subscript from '@/components/editor/SubscriptMark'
import FormattingClear from '@/components/editor/FormattingClear.js'
import FindAndReplace from '@/components/editor/FindAndReplace.js'
import generateUuid from '@/utils/uuid'

export default {
  name: 'TextEditor',
  components: {
    LinkPropertiesModal,
    Button,
    Icon,
    EditorContent,
    EditorMenuBar
  },
  props: {
    value: {
      type: String,
      required: true
    }
  },
  data () {
    const findAndReplace = new FindAndReplace()

    return {
      discriminator: generateUuid(),
      editor: process.browser
        ? new Editor({
          onUpdate: ({ getHTML }) => {
            this.$emit('input', getHTML())
          },
          extensions: [
            new Blockquote(),
            new BulletList(),
            new HardBreak(),
            new ListItem(),
            new OrderedList(),
            new Link(),
            new Bold(),
            new Italic(),
            new Strike(),
            new Underline(),
            new Superscript(),
            new Subscript(),
            new History(),
            new FormattingClear(),
            findAndReplace
          ],
          content: this.value
        })
        : null,
      showLinkModal: false,
      linkType: 'insert',
      linkProperties: {
        url: '',
        text: '',
        title: '',
        target: ''
      },
      findAndReplace,
      showFindAndReplace: false,
      searchTerm: '',
      replacement: ''
    }
  },
  watch: {
    value (newContent) {
      this.editor.setContent(newContent, false, { preserveWhitespace: 'full' })
    },
    'findAndReplace.options.caseSensitive' () {
      this.executeCommand(this.findAndReplace.find(this.searchTerm))
    },
    'findAndReplace.options.wholeWords' () {
      this.executeCommand(this.findAndReplace.find(this.searchTerm))
    }
  },
  beforeDestroy () {
    this.editor.destroy()
  },
  methods: {
    executeCommand (command) {
      command(this.editor.view.state, this.editor.view.dispatch)
    },
    openLinkModal (type, attributes) {
      this.linkType = type

      this.linkProperties = {
        url: attributes.href || '',
        title: attributes.title || '',
        target: attributes.target || ''
      }

      this.showLinkModal = true
    },
    applyLink () {
      const { url, title, target } = this.linkProperties

      const { commands } = this.editor

      if (url === '') {
        commands.link({ href: null })
      } else {
        commands.link({
          href: url,
          title: title === '' ? null : title,
          target: target === '' ? null : target
        })
      }

      this.showLinkModal = false
    }
  }
}
</script>

<style lang="scss">
.text-editor {
  border: 1px solid #ccc;
  border-radius: 3px;
  background: $entry-background;

  &__menu {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    background: $theme-color;
    color: $text-light;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;

    &-button {
      border-radius: 0;
      align-self: stretch;

      &--active {
        background: lighten($theme-color, 10%);
      }
    }

    &-separator {
      align-self: stretch;
      border-left: 1px solid $dark-background;
    }
  }

  &__find-and-replace {
    width: 100%;
    border-top: 1px solid $dark-background;
    padding: 4px 12px;

    &-row {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
    }

    input {
      width: auto;
      margin: 4px;
    }

    .button {
      padding: 5px 16px;
      margin: 4px;
    }
  }

  &__search-term {
    margin-right: 8px;
  }

  &__replacement {
    margin-right: 8px;
  }

  &__content .ProseMirror {
    padding: 0 16px;
    min-height: 4rem;
    overflow: auto;
    border-bottom-left-radius: 3px;
    border-bottom-right-radius: 3px;

    p {
      margin-top: .7em;
      margin-bottom: .7em;
    }

    a {
      text-decoration: underline;
      cursor: text;
      color: $theme-color;

      &:hover {
        color: $theme-color;
      }

      .text-editor__link--active {
        background: lighten($theme-color, 50%);
      }
    }
  }

  &__search-result {
    background: lighten($theme-color, 50%);

    &--active {
      background: #DB9D00;
    }
  }
}
</style>
