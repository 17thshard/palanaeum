export const KEY_CODES = {
  BACKSPACE: 8,
  ESCAPE: 27,
  SPACE: 32,
  DELETE: 46
}

export const hasOnlyModifiers = (event, modifiers) => {
  const others = ['ctrl', 'meta', 'shift', 'alt']
    .filter(key => !modifiers.includes(key))
    .reduce((acc, key) => acc || event[`${key}Key`], false)

  if (others) {
    return false
  }

  return modifiers.reduce((acc, key) => acc && event[`${key}Key`], true)
}
