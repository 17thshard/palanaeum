import { Mark, Plugin } from 'tiptap'
import { pasteRule, removeMark, updateMark } from 'tiptap-commands'
import { getMarkRange } from 'tiptap-utils'
import { Decoration, DecorationSet } from 'prosemirror-view'

export default class Link extends Mark {
  get name () {
    return 'link'
  }

  get schema () {
    return {
      attrs: {
        href: {
          default: null
        },
        title: {
          default: null
        },
        target: {
          default: null
        }
      },
      inclusive: false,
      parseDOM: [
        {
          tag: 'a[href]',
          getAttrs: dom => ({
            href: dom.getAttribute('href'),
            title: dom.getAttribute('title'),
            target: dom.getAttribute('target')
          })
        }
      ],
      toDOM: node => ['a', {
        ...node.attrs,
        rel: 'noopener noreferrer nofollow'
      }, 0]
    }
  }

  commands ({ type }) {
    return (attrs) => {
      if (attrs.href) {
        return updateMark(type, attrs)
      }

      return removeMark(type)
    }
  }

  pasteRules ({ type }) {
    return [
      pasteRule(
        /https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-zA-Z]{2,}\b([-a-zA-Z0-9@:%_+.~#?&//=]*)/g,
        type,
        url => ({ href: url })
      )
    ]
  }

  get plugins () {
    return [
      new Plugin({
        props: {
          decorations: ({ doc, selection, schema }) => {
            const { $cursor } = selection
            if (!$cursor) {
              return DecorationSet.empty
            }

            const range = getMarkRange($cursor, schema.marks.link)
            if (!range) {
              return DecorationSet.empty
            }

            return DecorationSet.create(
              doc,
              [Decoration.inline(range.from, range.to, {
                nodeName: 'span',
                class: 'text-editor__link--active'
              })]
            )
          }
        }
      })
    ]
  }
}
