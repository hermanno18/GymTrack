<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-950 text-white px-4">
    <div class="text-center space-y-4">
      <h1 class="text-4xl font-bold">
        <span class="text-cyan-400">Gym</span><span class="text-purple-400">Track</span>
      </h1>
      <p class="text-slate-400 max-w-md">
        Log your sets, reps, weight and distance. Watch your progression over time.
      </p>
      <div class="flex gap-3 justify-center pt-2">
        <NuxtLink to="/login" class="px-4 py-2 rounded-md bg-slate-800 hover:bg-slate-700 transition">
          Log in
        </NuxtLink>
        <NuxtLink to="/signup" class="px-4 py-2 rounded-md bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold transition">
          Sign up
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { loggedIn } = useUserSession()
if (loggedIn.value) {
  await navigateTo('/dashboard')
}
</script>
