<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="max-w-sm w-full card glow-border rounded-2xl overflow-hidden shadow-glow">
      <div class="relative h-32">
        <PhotoLayer filename="gym-hero.jpg" opacity="opacity-70" />
        <div class="absolute inset-0 bg-gradient-to-t from-panel via-panel/40 to-transparent" />
      </div>
      <form class="p-8 pt-6 space-y-5" @submit.prevent="submit">
        <h1 class="text-2xl font-bold text-accent">Welcome back</h1>

        <Transition name="fade">
          <div v-if="errorMessage" class="flex items-start gap-2 text-sm text-red-300 bg-red-950/60 border border-red-500/40 rounded-lg px-3 py-2">
            <Icon name="alert" class="w-4 h-4 mt-0.5 shrink-0" />
            <span>{{ errorMessage }}</span>
          </div>
        </Transition>

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

        <div>
          <label class="flex items-center gap-1.5 text-sm text-slate-400 mb-1" for="password">
            <Icon name="lock" class="w-3.5 h-3.5" /> Password
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2 focus:border-accent focus:outline-none transition"
          >
          <NuxtLink to="/forgot-password" class="block text-right text-xs text-slate-500 hover:text-accent mt-1">
            Forgot password?
          </NuxtLink>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="tap w-full py-3 rounded-lg bg-accent text-bg font-semibold hover:shadow-glow disabled:opacity-50 transition"
        >
          {{ loading ? 'Logging in…' : 'Log In' }}
        </button>

        <p class="text-sm text-slate-400">
          No account? <NuxtLink to="/signup" class="text-accent2 hover:underline">Register</NuxtLink>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')
const { fetch: refreshSession } = useUserSession()

async function submit() {
  loading.value = true
  errorMessage.value = ''
  try {
    await $fetch('/api/auth/login', {
      method: 'POST',
      body: { email: email.value, password: password.value },
    })
    await refreshSession()
    await navigateTo('/dashboard')
  } catch (err: any) {
    errorMessage.value = err?.data?.statusMessage || 'Something went wrong. Try again.'
  } finally {
    loading.value = false
  }
}
</script>
