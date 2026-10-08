<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="max-w-sm w-full card glow-border rounded-2xl p-8 space-y-5">
      <h1 class="text-2xl font-bold text-accent">Forgot password?</h1>
      <p class="text-sm text-slate-400">
        Enter your email and we'll send you a link to reset your password.
      </p>

      <Transition name="fade">
        <div v-if="message" class="flex items-start gap-2 text-sm text-accent bg-accent/10 border border-accent/30 rounded-lg px-3 py-2">
          <Icon name="check-circle" class="w-4 h-4 mt-0.5 shrink-0" />
          <span>{{ message }}</span>
        </div>
      </Transition>

      <Transition name="fade">
        <div v-if="errorMessage" class="flex items-start gap-2 text-sm text-red-300 bg-red-950/60 border border-red-500/40 rounded-lg px-3 py-2">
          <Icon name="alert" class="w-4 h-4 mt-0.5 shrink-0" />
          <span>{{ errorMessage }}</span>
        </div>
      </Transition>

      <form v-if="!message" class="space-y-5" @submit.prevent="submit">
        <div>
          <label class="flex items-center gap-1.5 text-sm text-slate-400 mb-1" for="email">
            <Icon name="mail" class="w-3.5 h-3.5" /> Email
          </label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2 focus:border-accent focus:outline-none transition"
          >
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="tap w-full py-3 rounded-lg bg-accent text-bg font-semibold hover:shadow-glow disabled:opacity-50 transition"
        >
          {{ loading ? 'Sending…' : 'Send reset link' }}
        </button>
      </form>

      <p class="text-sm text-slate-400">
        <NuxtLink to="/login" class="text-accent2 hover:underline">Back to login</NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const email = ref('')
const loading = ref(false)
const message = ref('')
const errorMessage = ref('')

async function submit() {
  loading.value = true
  errorMessage.value = ''
  try {
    await $fetch('/api/auth/forgot', { method: 'POST', body: { email: email.value } })
    // Same generic message whether or not the email is registered --
    // never let this form be used to probe which emails have accounts.
    message.value = 'If that email has an account, a reset link is on its way.'
  } catch (err: any) {
    // A 400 here only ever means "that's not a validly-formed email
    // address" (see forgotPasswordSchema) -- a real input mistake, not
    // an account-enumeration risk, so it's fine to surface directly.
    errorMessage.value = err?.data?.statusMessage || 'Something went wrong. Try again.'
  } finally {
    loading.value = false
  }
}
</script>
