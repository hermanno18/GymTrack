<template>
  <div class="min-h-screen bg-slate-950 text-white">
    <AppNav />
    <main class="max-w-3xl mx-auto px-6 py-10 space-y-8">
      <div v-if="pending" class="text-slate-400">Loading…</div>
      <template v-else-if="program">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold">{{ program.name }}</h1>
          <button class="text-sm text-red-400 hover:underline" @click="deleteProgram">
            Delete program
          </button>
        </div>

        <form class="flex gap-2" @submit.prevent="addDay">
          <input
            v-model="newDayName"
            type="text"
            placeholder="e.g. Day 1 — Push"
            required
            class="flex-1 rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
          <button
            type="submit"
            class="px-4 py-2 rounded-md bg-purple-500 hover:bg-purple-400 text-slate-950 font-semibold transition"
          >
            Add day
          </button>
        </form>

        <p v-if="errorMessage" class="text-sm text-red-400">{{ errorMessage }}</p>

        <section
          v-for="day in program.days"
          :key="day.id"
          class="rounded-lg bg-slate-900 border border-slate-800 p-5 space-y-4"
        >
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-lg">{{ day.name }}</h2>
            <button class="text-xs text-red-400 hover:underline" @click="deleteDay(day.id)">
              Remove day
            </button>
          </div>

          <ul class="space-y-2">
            <li
              v-for="exercise in day.exercises"
              :key="exercise.id"
              class="flex items-center justify-between rounded-md bg-slate-800 px-3 py-2 text-sm"
            >
              <span>
                {{ exercise.name }}
                <span class="text-slate-400">
                  — {{ formatTargets(exercise) }}
                </span>
              </span>
              <button class="text-red-400 hover:underline text-xs" @click="deleteExercise(exercise.id, day.id)">
                Remove
              </button>
            </li>
            <li v-if="!day.exercises.length" class="text-slate-500 text-sm">No exercises yet.</li>
          </ul>

          <form class="grid grid-cols-2 sm:grid-cols-5 gap-2" @submit.prevent="addExercise(day.id)">
            <input
              v-model="exerciseForms[day.id].name"
              type="text"
              placeholder="Exercise"
              required
              class="col-span-2 sm:col-span-1 rounded-md bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
            <input
              v-model="exerciseForms[day.id].targetSets"
              type="number"
              min="1"
              placeholder="Sets"
              class="rounded-md bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
            <input
              v-model="exerciseForms[day.id].targetReps"
              type="number"
              min="1"
              placeholder="Reps"
              class="rounded-md bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
            <input
              v-model="exerciseForms[day.id].targetWeightKg"
              type="number"
              min="0"
              step="0.5"
              placeholder="Weight (kg)"
              class="rounded-md bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
            <button
              type="submit"
              class="rounded-md bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition"
            >
              Add
            </button>
          </form>
        </section>
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

interface Exercise {
  id: number
  name: string
  targetSets: number | null
  targetReps: number | null
  targetWeightKg: number | null
  targetDistanceKm: number | null
}
interface Day {
  id: number
  name: string
  exercises: Exercise[]
}
interface Program {
  id: number
  name: string
  days: Day[]
}

const route = useRoute()
const programId = route.params.id

const { data: program, pending, refresh } = await useFetch<Program>(`/api/programs/${programId}`)
const newDayName = ref('')
const errorMessage = ref('')
const exerciseForms = reactive<Record<number, { name: string; targetSets: string; targetReps: string; targetWeightKg: string }>>({})

watchEffect(() => {
  for (const day of program.value?.days ?? []) {
    if (!exerciseForms[day.id]) {
      exerciseForms[day.id] = { name: '', targetSets: '', targetReps: '', targetWeightKg: '' }
    }
  }
})

function formatTargets(ex: Exercise) {
  const parts = []
  if (ex.targetSets) parts.push(`${ex.targetSets} sets`)
  if (ex.targetReps) parts.push(`${ex.targetReps} reps`)
  if (ex.targetWeightKg) parts.push(`${ex.targetWeightKg}kg`)
  if (ex.targetDistanceKm) parts.push(`${ex.targetDistanceKm}km`)
  return parts.length ? parts.join(' · ') : 'no target set'
}

async function addDay() {
  errorMessage.value = ''
  try {
    await $fetch(`/api/programs/${programId}/days`, { method: 'POST', body: { name: newDayName.value } })
    newDayName.value = ''
    await refresh()
  } catch (err: any) {
    errorMessage.value = err?.data?.statusMessage || 'Could not add day'
  }
}

async function deleteDay(dayId: number) {
  await $fetch(`/api/days/${dayId}`, { method: 'DELETE' })
  await refresh()
}

async function addExercise(dayId: number) {
  errorMessage.value = ''
  const form = exerciseForms[dayId]
  try {
    await $fetch(`/api/days/${dayId}/exercises`, {
      method: 'POST',
      body: {
        name: form.name,
        targetSets: form.targetSets || null,
        targetReps: form.targetReps || null,
        targetWeightKg: form.targetWeightKg || null,
      },
    })
    exerciseForms[dayId] = { name: '', targetSets: '', targetReps: '', targetWeightKg: '' }
    await refresh()
  } catch (err: any) {
    errorMessage.value = err?.data?.statusMessage || 'Could not add exercise'
  }
}

async function deleteExercise(exerciseId: number) {
  await $fetch(`/api/exercises/${exerciseId}`, { method: 'DELETE' })
  await refresh()
}

async function deleteProgram() {
  await $fetch(`/api/programs/${programId}`, { method: 'DELETE' })
  await navigateTo('/programs')
}
</script>
