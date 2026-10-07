<template>
  <div>
    <h1 class="text-2xl font-bold mb-6 flex items-center gap-2">
      <Icon name="dumbbell" class="w-6 h-6 text-accent" /> {{ day?.name }}
    </h1>
    <div v-if="pending" class="text-slate-400">Loading…</div>
    <LogSessionForm v-else-if="day" :day-id="day.id" :preset-exercises="day.exercises" />
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

interface Exercise { name: string; targetSets: number | null; targetReps: number | null; targetWeightKg: number | null }
interface Day { id: number; name: string; exercises: Exercise[] }

const route = useRoute()
const { data: day, pending } = await useFetch<Day>(`/api/days/${route.params.dayId}`)
</script>
