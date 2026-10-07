<template>
  <div class="min-h-screen bg-slate-950 text-white">
    <AppNav />
    <main class="max-w-3xl mx-auto px-6 py-10">
      <h1 class="text-2xl font-bold">Dashboard</h1>
      <p class="text-slate-400 mt-2">
        <NuxtLink to="/programs" class="text-cyan-400 hover:underline">Manage your programs</NuxtLink>
        to build a workout plan, or jump into logging a session.
      </p>
    </main>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
</script>
