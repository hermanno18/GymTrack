<template>
  <div>
    <div class="relative overflow-hidden rounded-2xl mb-6 p-6 md:p-8 card glow-border">
      <PhotoLayer filename="dashboard-banner.jpg" opacity="opacity-25" />
      <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/20 via-purple-500/20 to-bg/70" />
      <span class="hero-watermark absolute -right-6 -bottom-8 text-accent/10 pointer-events-none">
        <Icon name="dumbbell" class="w-40 h-40" />
      </span>
      <div class="relative flex items-center justify-between gap-4">
        <div>
          <p class="text-xs uppercase tracking-widest text-accent/80 mb-1">Let's move</p>
          <h1 class="text-2xl md:text-3xl font-extrabold">Ready to train?</h1>
        </div>
        <div class="flex items-center gap-2 bg-bg/60 rounded-full px-4 py-2 border border-fire/30">
          <span class="flame-icon text-fire"><Icon name="flame" class="w-5 h-5" /></span>
          <span class="font-bold text-lg">{{ summary?.totalWorkouts ?? 0 }}</span>
          <span class="text-xs text-slate-400">workout{{ summary?.totalWorkouts === 1 ? '' : 's' }} logged</span>
        </div>
      </div>
      <NuxtLink
        to="/log"
        class="tap relative mt-5 inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-accent to-accent2 text-bg font-bold pulse-cta"
      >
        <Icon name="dumbbell" class="w-5 h-5" /> Log a Workout
      </NuxtLink>
    </div>

    <div class="flex items-center justify-between mb-3">
      <h2 class="text-lg font-semibold flex items-center gap-2">
        <Icon name="clipboard" class="w-5 h-5 text-accent" /> Your Programs
      </h2>
      <NuxtLink to="/programs" class="text-sm text-accent hover:underline">+ New</NuxtLink>
    </div>

    <div v-if="programsPending" class="text-slate-400 text-sm mb-6">Loading…</div>
    <div v-else class="grid md:grid-cols-2 gap-4 mb-6">
      <TransitionGroup v-if="programs?.length" name="list">
        <NuxtLink
          v-for="program in programs"
          :key="program.id"
          :to="`/programs/${program.id}`"
          class="tap card glow-border rounded-2xl p-4 flex items-center justify-between hover:border-accent/60"
        >
          <span class="font-medium">{{ program.name }}</span>
        </NuxtLink>
      </TransitionGroup>
      <p v-else class="text-slate-400 text-sm col-span-2">
        No programs yet. <NuxtLink to="/programs" class="text-accent hover:underline">Start from scratch</NuxtLink> to get going.
      </p>
    </div>

    <div class="flex items-center justify-between mb-3">
      <h2 class="text-lg font-semibold flex items-center gap-2">
        <Icon name="calendar" class="w-5 h-5 text-accent2" /> Recent Sessions
      </h2>
      <NuxtLink v-if="recentSessions?.length" to="/history" class="text-sm text-accent hover:underline">See all &rarr;</NuxtLink>
    </div>
    <div v-if="sessionsPending" class="text-slate-400 text-sm">Loading…</div>
    <div v-else-if="recentSessions?.length" class="space-y-3">
      <SessionTile v-for="session in recentSessions" :key="session.id" :session="session" />
    </div>
    <div v-else class="card glow-border rounded-2xl p-4">
      <p class="text-slate-400 text-sm">No workouts logged yet — tap "Log a Workout" above to start your streak.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

const { data: programs, pending: programsPending } = await useFetch('/api/programs')
const { data: summary } = await useFetch('/api/dashboard/summary')
const { data: recentSessions, pending: sessionsPending } = await useFetch('/api/sessions', { query: { limit: 5 } })
</script>
