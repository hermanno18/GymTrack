const state = reactive({
  visible: false,
  message: '',
  resolve: null as ((value: boolean) => void) | null,
})

export function useConfirmState() {
  return state
}

export function useConfirm() {
  function confirm(message: string): Promise<boolean> {
    state.message = message
    state.visible = true
    return new Promise((resolve) => {
      state.resolve = resolve
    })
  }
  return { confirm }
}
