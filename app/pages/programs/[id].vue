<template>
  <div class="space-y-6">
    <div v-if="pending" class="text-slate-400">Loading…</div>
    <template v-else-if="program">
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold">{{ program.name }}</h1>
        <button class="tap text-sm text-red-400 flex items-center gap-1" @click="deleteProgram">
          <Icon name="trash" class="w-4 h-4" /> Delete program
        </button>
      </div>

      <form class="flex gap-2" @submit.prevent="addDay">
        <input
          v-model="newDayName"
          type="text"
          placeholder="e.g. Day 1 — Push"
          required
          class="flex-1 rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent2 focus:outline-none transition"
        >
        <button type="submit" class="tap px-4 py-2.5 rounded-lg bg-accent2 text-bg font-semibold hover:shadow-glow transition">
          <Icon name="plus" class="w-4 h-4 inline -mt-0.5" /> Add day
        </button>
      </form>

      <Transition name="fade">
        <p v-if="errorMessage" class="text-sm text-red-400">{{ errorMessage }}</p>
      </Transition>

      <TransitionGroup name="list" tag="div" class="space-y-4">
        <section
          v-for="day in program.days"
          :key="day.id"
          class="card glow-border rounded-2xl p-5 space-y-4"
        >
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-lg flex items-center gap-2">
              <Icon name="calendar" class="w-4 h-4 text-accent2" /> {{ day.name }}
            </h2>
            <button class="tap text-xs text-red-400 flex items-center gap-1" @click="deleteDay(day.id)">
              <Icon name="trash" class="w-3.5 h-3.5" /> Remove day
            </button>
          </div>

          <TransitionGroup name="list" tag="ul" class="space-y-2">
            <li
              v-for="exercise in day.exercises"
              :key="exercise.id"
              class="flex items-center justify-between rounded-lg bg-bg/60 border border-slate-800 px-3 py-2 text-sm"
            >
              <span class="flex items-center gap-2">
                <Icon name="dumbbell" class="w-4 h-4 text-accent shrink-0" />
                {{ exercise.name }}
                <span class="text-slate-500">— {{ formatTargets(exercise) }}</span>
              </span>
              <button class="tap text-red-400" aria-label="Remove exercise" @click="deleteExercise(exercise.id)">
                <Icon name="trash" class="w-4 h-4" />
              </button>
            </li>
          </TransitionGroup>
          <p v-if="!day.exercises.length" class="text-slate-500 text-sm">No exercises yet.</p>

          <form class="grid grid-cols-2 sm:grid-cols-5 gap-2" @submit.prevent="addExercise(day.id)">
            <input
              v-model="exerciseForms[day.id].name"
              type="text"
              placeholder="Exercise"
              required
              class="col-span-2 sm:col-span-1 rounded-lg bg-bg border border-slate-700 px-2 py-1.5 text-sm focus:border-accent focus:outline-none transition"
            >
            <input
              v-model="exerciseForms[day.id].targetSets"
              type="number"
              min="1"
              placeholder="Sets"
              class="rounded-lg bg-bg border border-slate-700 px-2 py-1.5 text-sm focus:border-accent focus:outline-none transition"
            >
            <input
              v-model="exerciseForms[day.id].targetReps"
              type="number"
              min="1"
              placeholder="Reps"
              class="rounded-lg bg-bg border border-slate-700 px-2 py-1.5 text-sm focus:border-accent focus:outline-none transition"
            >
            <input
              v-model="exerciseForms[day.id].targetWeight"
              type="number"
              min="0"
              step="0.5"
              :placeholder="`Weight (${weightUnit})`"
              class="rounded-lg bg-bg border border-slate-700 px-2 py-1.5 text-sm focus:border-accent focus:outline-none transition"
            >
            <button type="submit" class="tap rounded-lg bg-accent text-bg font-semibold text-sm hover:shadow-glow transition">
              Add
            </button>
          </form>
        </section>
      </TransitionGroup>

      <div v-if="!program.days.length" class="card glow-border rounded-2xl p-6 text-center text-slate-400 text-sm">
        No days yet. Add one above to start building the plan.
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

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
const { confirm } = useConfirm()

const { user } = useUserSession()
const weightUnit = computed(() => user.value?.weightUnit ?? 'kg')

const { data: program, pending, refresh } = await useFetch<Program>(`/api/programs/${programId}`)
const newDayName = ref('')
const errorMessage = ref('')
const exerciseForms = reactive<Record<number, { name: string; targetSets: string; targetReps: string; targetWeight: string }>>({})

watchEffect(() => {
  for (const day of program.value?.days ?? []) {
    if (!exerciseForms[day.id]) {
      exerciseForms[day.id] = { name: '', targetSets: '', targetReps: '', targetWeight: '' }
    }
  }
})

function formatTargets(ex: Exercise) {
  const parts = []
  if (ex.targetSets) parts.push(`${ex.targetSets} sets`)
  if (ex.targetReps) parts.push(`${ex.targetReps} reps`)
  const displayWeight = kgToDisplay(ex.targetWeightKg, weightUnit.value)
  if (displayWeight) parts.push(`${displayWeight}${weightUnit.value}`)
  const displayDistance = kmToDisplay(ex.targetDistanceKm, user.value?.distanceUnit ?? 'km')
  if (displayDistance) parts.push(`${displayDistance}${user.value?.distanceUnit ?? 'km'}`)
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
  if (!(await confirm('Remove this day and all its exercises?'))) return
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
        targetWeightKg: displayToKg(form.targetWeight, weightUnit.value),
      },
    })
    exerciseForms[dayId] = { name: '', targetSets: '', targetReps: '', targetWeight: '' }
    await refresh()
  } catch (err: any) {
    errorMessage.value = err?.data?.statusMessage || 'Could not add exercise'
  }
}

async function deleteExercise(exerciseId: number) {
  if (!(await confirm('Remove this exercise?'))) return
  await $fetch(`/api/exercises/${exerciseId}`, { method: 'DELETE' })
  await refresh()
}

async function deleteProgram() {
  if (!(await confirm('Delete this program and all its days/exercises?'))) return
  await $fetch(`/api/programs/${programId}`, { method: 'DELETE' })
  await navigateTo('/programs')
}
</script>
