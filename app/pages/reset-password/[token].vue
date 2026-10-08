<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="max-w-sm w-full card glow-border rounded-2xl p-8 space-y-5">
      <h1 class="text-2xl font-bold text-accent">Reset your password</h1>

      <Transition name="fade">
        <div v-if="errorMessage" class="flex items-start gap-2 text-sm text-red-300 bg-red-950/60 border border-red-500/40 rounded-lg px-3 py-2">
          <Icon name="alert" class="w-4 h-4 mt-0.5 shrink-0" />
          <span>{{ errorMessage }}</span>
        </div>
      </Transition>

      <Transition name="fade">
        <div v-if="success" class="flex items-start gap-2 text-sm text-accent bg-accent/10 border border-accent/30 rounded-lg px-3 py-2">
          <Icon name="check-circle" class="w-4 h-4 mt-0.5 shrink-0" />
          <span>Password reset. You can now log in.</span>
        </div>
      </Transition>

      <form v-if="!success" class="space-y-5" @submit.prevent="submit">
        <div>
          <label class="flex items-center gap-1.5 text-sm text-slate-400 mb-1" for="password">
            <Icon name="lock" class="w-3.5 h-3.5" /> New password
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            autocomplete="new-password"
            class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2 focus:border-accent focus:outline-none transition"
          >
        </div>
        <div>
          <label class="flex items-center gap-1.5 text-sm text-slate-400 mb-1" for="confirm">
            <Icon name="lock" class="w-3.5 h-3.5" /> Confirm password
          </label>
          <input
            id="confirm"
            v-model="confirmPassword"
            type="password"
            required
            autocomplete="new-password"
            class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2 focus:border-accent focus:outline-none transition"
          >
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="tap w-full py-3 rounded-lg bg-accent text-bg font-semibold hover:shadow-glow disabled:opacity-50 transition"
        >
          {{ loading ? 'Resetting…' : 'Reset password' }}
        </button>
      </form>

      <p class="text-sm text-slate-400">
        <NuxtLink to="/login" class="text-accent2 hover:underline">{{ success ? 'Go to login' : 'Back to login' }}</NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const token = route.params.token as string

const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const success = ref(false)

async function submit() {
  loading.value = true
  errorMessage.value = ''
  try {
    await $fetch('/api/auth/reset', {
      method: 'POST',
      body: { token, password: password.value, confirmPassword: confirmPassword.value },
    })
    success.value = true
  } catch (err: any) {
    errorMessage.value = err?.data?.statusMessage || 'Something went wrong. Try again.'
  } finally {
    loading.value = false
  }
}
</script>
