import { Mark } from 'tiptap'
import { toggleMark } from 'tiptap-commands'

export default class Subscript extends Mark {
  get name () {
    return 'subscript'
  }

  get schema () {
    return {
      parseDOM: [
        {
          tag: 'sub'
        },
        {
          style: 'vertical-align',
          getAttrs: value => value === 'sub'
        }
      ],
      toDOM: () => ['sub', 0]
    }
  }

  commands ({ type }) {
    return () => toggleMark(type)
  }
}
