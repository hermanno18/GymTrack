<template>
  <div class="space-y-4">
    <h1 class="text-2xl font-bold flex items-center gap-2">
      <Icon name="chart" class="w-6 h-6 text-accent" /> Progress
    </h1>

    <div v-if="pending" class="text-slate-400">Loading…</div>
    <template v-else-if="exercises?.length">
      <div class="relative">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
        <input
          v-model="query"
          type="text"
          placeholder="Search exercises..."
          autocomplete="off"
          class="w-full text-base rounded-lg bg-bg border border-slate-700 pl-9 pr-3 py-2.5 focus:border-accent focus:outline-none transition"
        >
      </div>

      <TransitionGroup name="list" tag="div" class="grid grid-cols-2 md:grid-cols-3 gap-3">
        <NuxtLink
          v-for="name in filtered"
          :key="name"
          :to="`/progress/${encodeURIComponent(name)}`"
          class="tap card glow-border rounded-2xl p-4 hover:border-accent transition flex items-center gap-2"
        >
          <Icon name="dumbbell" class="w-4 h-4 text-accent shrink-0" />
          <span class="font-medium text-sm truncate">{{ name }}</span>
        </NuxtLink>
      </TransitionGroup>
      <p v-if="!filtered.length" class="text-slate-500 text-sm">No exercises match your search.</p>
    </template>
    <p v-else class="text-slate-400">Log a few workouts first, then come back here to see your progress charts.</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

const { data, pending } = await useFetch<{ exercises: string[] }>('/api/progress/exercises')
const exercises = computed(() => data.value?.exercises ?? [])

const query = ref('')
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return exercises.value
  return exercises.value.filter((name) => name.toLowerCase().includes(q))
})
</script>
