<template>
  <div>
    <h1 class="text-2xl font-bold mb-6 flex items-center gap-2">
      <Icon name="dumbbell" class="w-6 h-6 text-accent" /> Log a Workout
    </h1>

    <div v-if="pending" class="text-slate-400">Loading…</div>
    <template v-else>
      <div v-for="program in programsWithDays" :key="program.id" class="card glow-border rounded-2xl p-6 mb-4">
        <h2 class="font-semibold text-accent mb-3">{{ program.name }}</h2>
        <div class="space-y-1.5">
          <NuxtLink
            v-for="day in program.days"
            :key="day.id"
            :to="`/log/${day.id}`"
            class="tap flex items-center gap-3 bg-bg/40 hover:bg-bg/70 rounded-xl px-3 py-2.5 transition"
          >
            <span class="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-accent2 text-bg flex items-center justify-center shrink-0">
              <Icon name="play" class="w-3.5 h-3.5" />
            </span>
            <span class="text-sm font-medium truncate">{{ day.name }}</span>
          </NuxtLink>
        </div>
      </div>

      <div class="card glow-border rounded-2xl p-6">
        <h2 class="font-semibold text-accent2 mb-2">Free-form Session</h2>
        <p class="text-sm text-slate-400 mb-4">Not following a specific day? Log whatever you did.</p>
        <NuxtLink
          to="/log/adhoc"
          class="tap inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-accent2 text-white font-semibold hover:shadow-glow transition"
        >
          <Icon name="plus" class="w-4 h-4" /> Log Free-form
        </NuxtLink>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

interface Day { id: number; name: string }
interface Program { id: number; name: string; days: Day[] }

const { data: programs, pending } = await useFetch<Program[]>('/api/programs/with-days')
const programsWithDays = computed(() => (programs.value ?? []).filter((p) => p.days.length))
</script>
