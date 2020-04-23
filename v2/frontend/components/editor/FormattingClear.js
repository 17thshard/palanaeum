import { Extension } from 'tiptap'
import { getMarkRange } from 'tiptap-utils'

export default class FormattingClear extends Extension {
  get name () {
    return 'clearFormatting'
  }

  commands ({ schema }) {
    return () => {
      return function ({ tr, selection }, dispatch) {
        const { $from, empty } = selection

        if (empty) {
          Object.values(schema.marks).forEach((mark) => {
            const { from, to } = getMarkRange($from, mark)
            tr.removeMark(from, to, mark)
          })
        } else {
          const { from, to } = selection
          Object.values(schema.marks).forEach((mark) => {
            tr.removeMark(from, to, mark)
          })
        }

        return dispatch(tr)
      }
    }
  }
}
