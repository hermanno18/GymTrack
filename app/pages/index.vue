<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="max-w-sm w-full card glow-border rounded-2xl overflow-hidden shadow-glow text-center">
      <div class="relative h-40">
        <PhotoLayer filename="gym-hero.jpg" opacity="opacity-70" />
        <div class="absolute inset-0 bg-gradient-to-t from-panel via-panel/40 to-transparent" />
        <span class="hero-watermark absolute -right-4 -bottom-4 text-accent/20 pointer-events-none">
          <Icon name="dumbbell" class="w-24 h-24" />
        </span>
      </div>
      <div class="p-8 pt-6 space-y-4">
        <h1 class="text-3xl font-extrabold">
          <span class="text-accent">Gym</span><span class="text-accent2">Track</span>
        </h1>
        <p class="text-slate-400 text-sm">
          Log your sets, reps, weight and distance. Watch your progression over time.
        </p>
        <div class="flex gap-3 justify-center pt-2">
          <NuxtLink to="/login" class="tap px-4 py-2.5 rounded-lg bg-slate-700 hover:bg-slate-600 transition font-medium">
            Log in
          </NuxtLink>
          <NuxtLink to="/signup" class="tap px-4 py-2.5 rounded-lg bg-accent text-bg font-semibold hover:shadow-glow transition">
            Sign up
          </NuxtLink>
        </div>
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
