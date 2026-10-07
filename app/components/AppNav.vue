<template>
  <nav class="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
    <NuxtLink to="/dashboard" class="font-bold text-lg">
      <span class="text-cyan-400">Gym</span><span class="text-purple-400">Track</span>
    </NuxtLink>
    <div class="flex items-center gap-4 text-sm text-slate-300">
      <NuxtLink to="/programs" class="hover:text-white">Programs</NuxtLink>
      <span>{{ user?.email }}</span>
      <button class="text-cyan-400 hover:underline" @click="logout">Log out</button>
    </div>
  </nav>
</template>

<script setup lang="ts">
const { user, clear } = useUserSession()

async function logout() {
  await clear()
  await navigateTo('/login')
}
</script>
