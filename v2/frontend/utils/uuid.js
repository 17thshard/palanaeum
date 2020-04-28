export default function generateUuid () {
  return Math.random().toString(36).substr(2, 9)
}
