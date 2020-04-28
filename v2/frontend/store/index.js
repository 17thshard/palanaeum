export const state = () => ({
  audioLock: null
})

export const mutations = {
  acquireAudioLock (state, id) {
    state.audioLock = id
  },
  releaseAudioLock (state) {
    state.audioLock = null
  }
}
