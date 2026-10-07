<template>
  <div>
    <h1 class="text-2xl font-bold mb-6 flex items-center gap-2">
      <Icon name="calendar" class="w-6 h-6 text-accent" /> Workout History
    </h1>

    <div v-if="pending" class="text-slate-400">Loading…</div>
    <div v-else-if="sessions?.length" class="space-y-3">
      <SessionTile v-for="session in sessions" :key="session.id" :session="session" />
    </div>
    <div v-else class="relative overflow-hidden rounded-2xl card glow-border p-8 text-center">
      <PhotoLayer filename="empty-history.jpg" opacity="opacity-20" />
      <div class="absolute inset-0 bg-gradient-to-b from-transparent to-bg/80" />
      <div class="relative">
        <p class="text-slate-300 font-medium mb-1">No sessions logged yet</p>
        <p class="text-slate-400 text-sm">Your workout history starts the moment you log one.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

const { data: sessions, pending } = await useFetch('/api/sessions')
</script>
