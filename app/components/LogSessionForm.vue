<template>
  <form class="space-y-5" @submit.prevent="submit">
    <div class="card glow-border rounded-2xl p-4 md:p-6">
      <label class="block text-xs text-slate-400 mb-1">Date</label>
      <input
        v-model="performedAt"
        type="date"
        required
        class="w-full text-base rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent focus:outline-none transition"
      >
    </div>

    <Transition name="fade">
      <p v-if="errorMessage" class="text-sm text-red-400">{{ errorMessage }}</p>
    </Transition>

    <TransitionGroup name="list" tag="div" class="space-y-3">
      <div v-for="(row, i) in rows" :key="row.key" class="card glow-border rounded-2xl p-4">
        <div class="flex items-center justify-between mb-3 gap-2">
          <input
            v-if="row.editableName"
            v-model="row.name"
            type="text"
            placeholder="Exercise name"
            required
            class="flex-1 font-semibold bg-transparent border-b border-slate-700 focus:border-accent focus:outline-none transition"
          >
          <p v-else class="font-semibold">{{ row.name }}</p>
          <button type="button" class="tap text-red-400 shrink-0" aria-label="Remove exercise" @click="rows.splice(i, 1)">
            <Icon name="trash" class="w-4 h-4" />
          </button>
        </div>
        <p v-if="row.targetHint" class="text-xs text-slate-500 mb-3">Target: {{ row.targetHint }}</p>
        <div class="grid grid-cols-4 gap-2">
          <div>
            <label class="block text-[11px] text-slate-500 mb-1">Sets</label>
            <input v-model="row.sets" type="number" min="1" inputmode="numeric" class="w-full text-base text-center rounded-lg bg-bg border border-slate-700 py-2.5 focus:border-accent focus:outline-none transition">
          </div>
          <div>
            <label class="block text-[11px] text-slate-500 mb-1">Reps</label>
            <input v-model="row.reps" type="number" min="0" inputmode="numeric" class="w-full text-base text-center rounded-lg bg-bg border border-slate-700 py-2.5 focus:border-accent focus:outline-none transition">
          </div>
          <div>
            <label class="block text-[11px] text-slate-500 mb-1">Wt (kg)</label>
            <input v-model="row.weightKg" type="number" min="0" step="0.5" inputmode="decimal" class="w-full text-base text-center rounded-lg bg-bg border border-slate-700 py-2.5 focus:border-accent focus:outline-none transition">
          </div>
          <div>
            <label class="block text-[11px] text-slate-500 mb-1">Dist (km)</label>
            <input v-model="row.distanceKm" type="number" min="0" step="0.1" inputmode="decimal" class="w-full text-base text-center rounded-lg bg-bg border border-slate-700 py-2.5 focus:border-accent focus:outline-none transition">
          </div>
        </div>
      </div>
    </TransitionGroup>

    <button
      type="button"
      class="tap w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-dashed border-slate-700 text-slate-400 hover:text-accent2 hover:border-accent2 transition"
      @click="addRow"
    >
      <Icon name="plus" class="w-4 h-4" /> Add exercise
    </button>

    <button
      type="submit"
      :disabled="submitting || !rows.length"
      class="tap pulse-cta w-full py-4 rounded-xl bg-gradient-to-r from-accent to-accent2 text-bg font-bold text-lg flex items-center justify-center gap-2 disabled:opacity-50"
    >
      <Icon name="check-circle" class="w-5 h-5" /> {{ submitting ? 'Saving…' : 'Save Workout' }}
    </button>
  </form>
</template>

<script setup lang="ts">
interface PresetExercise {
  name: string
  targetSets: number | null
  targetReps: number | null
  targetWeightKg: number | null
}
interface Row {
  key: number
  name: string
  editableName: boolean
  sets: string
  reps: string
  weightKg: string
  distanceKm: string
  targetHint: string
}

const props = defineProps<{ dayId: number | null; presetExercises?: PresetExercise[] }>()

let keyCounter = 0
function makeRow(partial: Partial<Row> = {}): Row {
  return {
    key: keyCounter++,
    name: '',
    editableName: true,
    sets: '1',
    reps: '',
    weightKg: '',
    distanceKm: '',
    targetHint: '',
    ...partial,
  }
}

function targetHintFor(ex: PresetExercise) {
  const parts = []
  if (ex.targetSets) parts.push(`${ex.targetSets} sets`)
  if (ex.targetReps) parts.push(`${ex.targetReps} reps`)
  if (ex.targetWeightKg) parts.push(`${ex.targetWeightKg}kg`)
  return parts.join(' · ')
}

const rows = ref<Row[]>(
  (props.presetExercises ?? []).map((ex) =>
    makeRow({
      name: ex.name,
      editableName: false,
      sets: String(ex.targetSets ?? 1),
      reps: ex.targetReps ? String(ex.targetReps) : '',
      weightKg: ex.targetWeightKg ? String(ex.targetWeightKg) : '',
      targetHint: targetHintFor(ex),
    }),
  ),
)

function addRow() {
  rows.value.push(makeRow())
}

const today = new Date().toISOString().slice(0, 10)
const performedAt = ref(today)
const submitting = ref(false)
const errorMessage = ref('')

async function submit() {
  submitting.value = true
  errorMessage.value = ''
  try {
    await $fetch('/api/sessions', {
      method: 'POST',
      body: {
        programDayId: props.dayId,
        performedAt: performedAt.value,
        exercises: rows.value
          .filter((r) => r.name.trim())
          .map((r) => ({
            name: r.name.trim(),
            sets: Number(r.sets) || 1,
            reps: r.reps ? Number(r.reps) : null,
            weightKg: r.weightKg ? Number(r.weightKg) : null,
            distanceKm: r.distanceKm ? Number(r.distanceKm) : null,
          })),
      },
    })
    await navigateTo('/history')
  } catch (err: any) {
    errorMessage.value = err?.data?.statusMessage || 'Could not save workout'
  } finally {
    submitting.value = false
  }
}
</script>
