<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="state.visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
        @click.self="cancel"
      >
        <div class="card glow-border rounded-2xl p-6 max-w-sm w-full">
          <p class="text-sm text-slate-200 mb-6">{{ state.message }}</p>
          <div class="flex gap-3">
            <button type="button" class="tap flex-1 py-2.5 rounded-lg bg-slate-700 hover:bg-slate-600 font-medium" @click="cancel">
              Cancel
            </button>
            <button type="button" class="tap flex-1 py-2.5 rounded-lg bg-red-500 hover:bg-red-600 text-white font-semibold" @click="confirmed">
              Confirm
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const state = useConfirmState()

function cancel() {
  state.visible = false
  state.resolve?.(false)
  state.resolve = null
}
function confirmed() {
  state.visible = false
  state.resolve?.(true)
  state.resolve = null
}
</script>
