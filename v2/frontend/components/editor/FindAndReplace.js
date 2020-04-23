import { Extension, Plugin } from 'tiptap'
import { Decoration, DecorationSet } from 'prosemirror-view'

export default class FindAndReplace extends Extension {
  constructor (options = {}) {
    super(options)

    this.results = []
    this.activeResult = null
    this.lastSearchTerm = null
    this.searchTerm = null
    this._updating = false
  }

  get name () {
    return 'search'
  }

  get defaultOptions () {
    return {
      searching: false,
      caseSensitive: false,
      disableRegex: true,
      alwaysSearch: false,
      wholeWords: false
    }
  }

  commands () {
    return {
      find: attrs => this.find(attrs),
      replace: attrs => this.replace(attrs),
      replaceAll: attrs => this.replaceAll(attrs),
      clearSearch: () => this.clear()
    }
  }

  get findRegExp () {
    return RegExp(
      this.options.wholeWords ? `(?<=^|\\s)${this.searchTerm}(?=$|\\s)` : this.searchTerm,
      !this.options.caseSensitive ? 'gui' : 'gu'
    )
  }

  get decorations () {
    return this.results.map((deco, index) => (
      Decoration.inline(
        deco.from,
        deco.to,
        {
          class: index === this.activeResult
            ? 'text-editor__search-result text-editor__search-result--active'
            : 'text-editor__search-result'
        }
      )
    ))
  }

  _search (doc) {
    this.results = []
    if (this.searchTerm !== this.lastSearchTerm) {
      this.activeResult = null
    }
    const mergedTextNodes = []
    let index = 0

    if (!this.searchTerm) {
      return
    }

    doc.descendants((node, pos) => {
      if (node.isText) {
        if (mergedTextNodes[index]) {
          mergedTextNodes[index] = {
            text: mergedTextNodes[index].text + node.text,
            pos: mergedTextNodes[index].pos
          }
        } else {
          mergedTextNodes[index] = {
            text: node.text,
            pos
          }
        }
      } else {
        index += 1
      }
    })

    mergedTextNodes.forEach(({ text, pos }) => {
      const search = this.findRegExp
      let m
      // eslint-disable-next-line no-cond-assign
      while ((m = search.exec(text))) {
        if (m[0] === '') {
          break
        }

        this.results.push({
          from: pos + m.index,
          to: pos + m.index + m[0].length
        })
        if (this.searchTerm !== this.lastSearchTerm) {
          this.activeResult = 0
        }
      }
    })

    this.lastSearchTerm = this.searchTerm
  }

  replace (replace) {
    return (state, dispatch) => {
      if (this.results.length === 0) {
        return
      }
      const { from, to } = this.results[this.activeResult]
      dispatch(state.tr.insertText(replace, from, to))

      const offset = to - from - replace.length
      this.results.forEach((result, index) => {
        if (index > this.activeResult) {
          result.from = result.from - offset
          result.to = result.to - offset
        }
      })

      this.results.splice(this.activeResult, 1)
      this.activeResult = this.activeResult - 1
      this.nextResult(this.searchTerm)(this.editor.view.state, this.editor.view.dispatch)
    }
  }

  rebaseNextResult (replace, index, lastOffset = 0) {
    const nextIndex = index + 1

    if (!this.results[nextIndex]) {
      return null
    }

    const { from: currentFrom, to: currentTo } = this.results[index]
    const offset = (currentTo - currentFrom - replace.length) + lastOffset
    const { from, to } = this.results[nextIndex]

    this.results[nextIndex] = {
      to: to - offset,
      from: from - offset
    }

    return offset
  }

  replaceAll (replace) {
    return ({ tr }, dispatch) => {
      let offset

      if (!this.results.length) {
        return
      }

      this.results.forEach(({ from, to }, index) => {
        tr.insertText(replace, from, to)
        offset = this.rebaseNextResult(replace, index, offset)
      })

      dispatch(tr)

      this.editor.commands.find(this.searchTerm)
    }
  }

  find (searchTerm) {
    return (state, dispatch) => {
      this.searchTerm = this.options.disableRegex
        ? searchTerm.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')
        : searchTerm

      this.updateView(state, dispatch)
    }
  }

  clear () {
    return (state, dispatch) => {
      this.searchTerm = null

      this.updateView(state, dispatch)
    }
  }

  prevResult (searchTerm) {
    return (state, dispatch) => {
      if (this.results.length === 0) {
        this.find(searchTerm)(state, dispatch)
      }

      if (this.results.length === 0) {
        return
      }

      this.activeResult = (this.results.length + this.activeResult - 1) % this.results.length

      this.updateView(state, dispatch)
    }
  }

  nextResult (searchTerm) {
    return (state, dispatch) => {
      if (this.results.length === 0) {
        this.find(searchTerm)(state, dispatch)
      }

      if (this.results.length === 0) {
        return
      }

      this.activeResult = (this.activeResult + 1) % this.results.length

      this.updateView(this.editor.view.state, this.editor.view.dispatch)
    }
  }

  updateView ({ tr }, dispatch) {
    this._updating = true
    dispatch(tr)
    this._updating = false
  }

  createDeco (doc) {
    this._search(doc)
    return this.decorations
      ? DecorationSet.create(doc, this.decorations)
      : []
  }

  get plugins () {
    return [
      new Plugin({
        state: {
          init () {
            return DecorationSet.empty
          },
          apply: (tr, old) => {
            if (this._updating || this.options.searching || (tr.docChanged && this.options.alwaysSearch)) {
              return this.createDeco(tr.doc)
            }

            if (tr.docChanged) {
              return old.map(tr.mapping, tr.doc)
            }

            return old
          }
        },
        props: {
          decorations (state) {
            return this.getState(state)
          }
        }
      })
    ]
  }
}
