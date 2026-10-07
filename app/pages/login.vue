<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-950 px-4">
    <form
      class="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-xl p-8 space-y-5"
      @submit.prevent="submit"
    >
      <div>
        <h1 class="text-2xl font-bold text-white">Log in to GymTrack</h1>
        <p class="text-slate-400 text-sm mt-1">Track your progress, one session at a time.</p>
      </div>

      <div v-if="errorMessage" class="text-sm text-red-400 bg-red-950/50 border border-red-900 rounded-md px-3 py-2">
        {{ errorMessage }}
      </div>

      <div class="space-y-1">
        <label class="text-sm text-slate-300" for="email">Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          required
          autocomplete="email"
          class="w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
        >
      </div>

      <div class="space-y-1">
        <label class="text-sm text-slate-300" for="password">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          class="w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
        >
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full rounded-md bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold py-2 transition"
      >
        {{ loading ? 'Logging in…' : 'Log in' }}
      </button>

      <p class="text-sm text-slate-400 text-center">
        No account yet?
        <NuxtLink to="/signup" class="text-cyan-400 hover:underline">Sign up</NuxtLink>
      </p>
    </form>
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
