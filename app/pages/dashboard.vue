<template>
  <div class="min-h-screen bg-slate-950 text-white">
    <nav class="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
      <span class="font-bold text-lg">GymTrack</span>
      <div class="flex items-center gap-4 text-sm text-slate-300">
        <span>{{ user?.email }}</span>
        <button class="text-cyan-400 hover:underline" @click="logout">Log out</button>
      </div>
    </nav>
    <main class="max-w-3xl mx-auto px-6 py-10">
      <h1 class="text-2xl font-bold">Dashboard</h1>
      <p class="text-slate-400 mt-2">
        You're logged in. Program builder and workout logging land here next.
      </p>
    </main>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { user, clear } = useUserSession()

async function logout() {
  await clear()
  await navigateTo('/login')
}
</script>
