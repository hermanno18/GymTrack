<template>
  <div>
    <NuxtLink to="/history" class="text-sm text-accent hover:underline mb-4 inline-block">&larr; Back to history</NuxtLink>
    <div v-if="pending" class="text-slate-400">Loading…</div>
    <template v-else-if="session">
      <h1 class="text-2xl font-bold mb-1">{{ session.dayName }}</h1>
      <p class="text-slate-500 text-sm mb-6">{{ formattedDate }}</p>

      <div class="space-y-3">
        <div v-for="exercise in session.exercises" :key="exercise.name" class="card glow-border rounded-2xl p-4">
          <p class="font-semibold mb-2 flex items-center gap-2">
            <Icon name="dumbbell" class="w-4 h-4 text-accent" /> {{ exercise.name }}
          </p>
          <ul class="space-y-1 text-sm text-slate-400">
            <li v-for="set in exercise.sets" :key="set.id" class="flex gap-3">
              <span class="text-slate-600 w-12 shrink-0">Set {{ set.setNumber }}</span>
              <span>{{ formatSet(set) }}</span>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

interface SetRow { id: number; setNumber: number; reps: number | null; weightKg: number | null; distanceKm: number | null }
interface ExerciseGroup { name: string; sets: SetRow[] }
interface SessionDetail { id: number; performedAt: string; dayName: string; exercises: ExerciseGroup[] }

const route = useRoute()
const { data: session, pending } = await useFetch<SessionDetail>(`/api/sessions/${route.params.id}`)

const formattedDate = computed(() => {
  if (!session.value) return ''
  return formatSessionDate(session.value.performedAt, { dateStyle: 'full', timeStyle: 'short' })
})

function formatSet(set: SetRow) {
  const parts = []
  if (set.reps) parts.push(`${set.reps} reps`)
  if (set.weightKg) parts.push(`${set.weightKg}kg`)
  if (set.distanceKm) parts.push(`${set.distanceKm}km`)
  return parts.length ? parts.join(' · ') : '—'
}
</script>
