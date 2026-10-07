<template>
  <div class="max-w-lg mx-auto">
    <div v-if="pending" class="text-slate-400 text-center py-12">Loading…</div>
    <div v-else-if="loadError" class="card glow-border rounded-2xl p-6 text-center text-slate-400 text-sm">
      {{ loadError }}
    </div>
    <template v-else-if="exercises.length">
      <!-- WORK / REST screen -->
      <div v-if="phase !== 'summary'">
        <div class="flex items-center justify-between mb-4">
          <h1 class="text-xl font-bold flex items-center gap-2">
            <Icon name="dumbbell" class="w-5 h-5 text-accent" /> {{ dayName }}
          </h1>
          <span class="text-xs text-slate-500">Exercise {{ Math.min(index + 1, exercises.length) }} of {{ exercises.length }}</span>
        </div>

        <div class="flex gap-1.5 mb-6">
          <span
            v-for="(_, i) in exercises"
            :key="i"
            class="h-1.5 flex-1 rounded-full"
            :class="i < index ? 'bg-accent' : i === index ? 'bg-accent2' : 'bg-slate-700'"
          />
        </div>

        <div class="card glow-border rounded-2xl p-6 text-center">
          <p
            class="text-xs uppercase tracking-widest font-semibold mb-1"
            :class="phase === 'work' ? 'text-accent' : 'text-fire'"
          >
            {{ phase === 'work' ? 'WORKING' : 'RESTING' }}
          </p>
          <h2 class="text-2xl font-bold mb-1">{{ phase === 'work' ? currentExercise.name : 'Take a breather' }}</h2>
          <p class="text-sm text-slate-400 mb-1">{{ phase === 'work' ? targetSummary : 'Ready when you are -- no rush.' }}</p>
          <p class="text-xs text-accent2 font-semibold mb-1">{{ setLabel }}</p>
          <p class="text-[11px] text-slate-500 mb-4">{{ nextUpLabel }}</p>

          <div
            class="mx-auto mb-6 w-44 h-44 rounded-full flex items-center justify-center border-4 transition-colors duration-500"
            :class="phase === 'work' ? 'border-accent shadow-glow' : 'border-fire'"
          >
            <span class="text-4xl font-mono font-bold tabular-nums">{{ formatTimer(elapsedSeconds) }}</span>
          </div>

          <div v-if="phase === 'work'" class="grid grid-cols-2 gap-2 mb-6 text-sm">
            <div>
              <label class="block text-[11px] text-slate-500 mb-1">Sets done</label>
              <input v-model="entry.sets" type="number" class="w-full text-base text-center rounded-lg bg-bg border border-slate-700 py-2">
            </div>
            <div>
              <label class="block text-[11px] text-slate-500 mb-1">Reps</label>
              <input v-model="entry.reps" type="number" class="w-full text-base text-center rounded-lg bg-bg border border-slate-700 py-2">
            </div>
            <div>
              <label class="block text-[11px] text-slate-500 mb-1">Weight ({{ weightUnit }})</label>
              <input v-model="entry.weight" type="number" step="0.1" class="w-full text-base text-center rounded-lg bg-bg border border-slate-700 py-2">
            </div>
            <div>
              <label class="block text-[11px] text-slate-500 mb-1">Distance ({{ distanceUnit }})</label>
              <input v-model="entry.distance" type="number" step="0.1" class="w-full text-base text-center rounded-lg bg-bg border border-slate-700 py-2">
            </div>
          </div>

          <div v-if="phase === 'work'">
            <button
              type="button"
              class="tap pulse-cta w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 bg-gradient-to-r from-accent to-accent2 text-bg"
              @click="startRestPhase"
            >
              <Icon name="mail" class="w-5 h-5" /> Rest
            </button>
            <button type="button" class="tap w-full mt-2 py-2 text-sm text-slate-500 hover:text-accent transition" @click="finishExerciseAndAdvance">
              Skip rest &rarr; {{ isLast ? 'finish workout' : 'next exercise' }}
            </button>
          </div>
          <div v-else class="grid grid-cols-2 gap-3">
            <button
              type="button"
              class="tap w-full py-4 rounded-xl font-bold flex items-center justify-center gap-1.5 bg-bg border-2 border-accent text-accent"
              @click="goToNextSet"
            >
              <Icon name="dumbbell" class="w-4 h-4" /> Next Set
            </button>
            <button
              type="button"
              class="tap w-full py-4 rounded-xl font-bold flex items-center justify-center gap-1.5 bg-gradient-to-r from-fire to-accent2 text-bg"
              @click="finishExerciseAndAdvance"
            >
              {{ isLast ? 'Finish Workout' : 'Next Exercise' }}
            </button>
          </div>
        </div>
      </div>

      <!-- SUMMARY / FINISH screen -->
      <div v-else class="card glow-border rounded-2xl p-6 text-center">
        <span class="inline-flex text-fire mb-2"><Icon name="trophy" class="w-12 h-12" /></span>
        <h2 class="text-2xl font-bold mb-1">Workout Complete!</h2>
        <p class="text-sm text-slate-400 mb-6">
          {{ exercises.length }} exercises &middot; {{ formatTimer(totalWork) }} working &middot; {{ formatTimer(totalRest) }} resting
        </p>
        <button
          type="button"
          :disabled="saving"
          class="tap pulse-cta w-full py-4 rounded-xl bg-gradient-to-r from-accent to-accent2 text-bg font-bold text-lg flex items-center justify-center gap-2 disabled:opacity-50"
          @click="save"
        >
          <Icon name="check-circle" class="w-5 h-5" /> {{ saving ? 'Saving…' : 'Save & View My Story' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

interface GuidedExercise {
  id: number
  name: string
  targetSets: number | null
  targetReps: number | null
  targetWeightKg: number | null
  targetDistanceKm: number | null
  prWeightKg: number | null
  prReps: number | null
  prDistanceKm: number | null
}
interface Result {
  name: string
  startedAt: string | null
  workSeconds: number
  restSeconds: number
  sets: string
  reps: string
  weightKg: number | null
  distanceKm: number | null
}

const route = useRoute()
const dayId = route.params.dayId as string
const { user } = useUserSession()
const weightUnit = computed(() => user.value?.weightUnit ?? 'kg')
const distanceUnit = computed(() => user.value?.distanceUnit ?? 'km')

const pending = ref(true)
const loadError = ref('')
const dayName = ref('')
const exercises = ref<GuidedExercise[]>([])

onMounted(async () => {
  try {
    const data = await $fetch<{ day: { name: string }; exercises: GuidedExercise[] }>(`/api/guided/${dayId}`)
    dayName.value = data.day.name
    exercises.value = data.exercises
    boot()
  } catch (err: any) {
    loadError.value = err?.data?.statusMessage || 'Could not start this guided session'
  } finally {
    pending.value = false
  }
})

const index = ref(0)
const phase = ref<'work' | 'rest' | 'summary'>('work')
const currentSet = ref(1)
const accumulatedWork = ref(0)
const accumulatedRest = ref(0)
const results = ref<Result[]>([])
const sessionStartClock = ref(formatHM(new Date()))
const exerciseStartedAtClock = ref<string | null>(null)
const phaseStartedAt = ref(Date.now())
const elapsedSeconds = ref(0)
const saving = ref(false)

const entry = reactive({ sets: '1', reps: '', weight: '', distance: '' })

const currentExercise = computed(() => exercises.value[index.value])
const isLast = computed(() => index.value === exercises.value.length - 1)

// Merges the coach's static plan with the user's best-ever logged
// numbers -- PR wins when present, so the countdown shows "beat your own
// record" once there's history, falling back to the coach's plan otherwise.
function effectiveTarget(ex: GuidedExercise) {
  const isPR = ex.prWeightKg != null || ex.prDistanceKm != null
  return {
    sets: ex.targetSets,
    reps: isPR && ex.prReps ? ex.prReps : ex.targetReps,
    weightKg: ex.prWeightKg ?? ex.targetWeightKg,
    distanceKm: ex.prDistanceKm ?? ex.targetDistanceKm,
    isPR,
  }
}

const targetSummary = computed(() => {
  const ex = currentExercise.value
  if (!ex) return ''
  const t = effectiveTarget(ex)
  const parts: string[] = []
  if (t.sets || t.reps) parts.push(`${t.sets || '-'} \u00d7 ${t.reps || '-'}`)
  const dispWeight = kgToDisplay(t.weightKg, weightUnit.value)
  if (dispWeight != null) parts.push(`${dispWeight} ${weightUnit.value}`)
  const dispDistance = kmToDisplay(t.distanceKm, distanceUnit.value)
  if (dispDistance != null) parts.push(`${dispDistance} ${distanceUnit.value}`)
  const prefix = t.isPR ? '\ud83c\udfc6 Beat your best: ' : 'Target: '
  return parts.length ? prefix + parts.join(' \u00b7 ') : 'No specific target -- just go!'
})

const setLabel = computed(() => {
  const ex = currentExercise.value
  if (!ex) return ''
  return ex.targetSets ? `Set ${currentSet.value} of ${ex.targetSets}` : `Set ${currentSet.value}`
})

const nextUpLabel = computed(() => {
  const upcoming = exercises.value[index.value + 1]
  return upcoming ? `Up next: ${upcoming.name}` : 'Last exercise -- almost there!'
})

const totalWork = computed(() => results.value.reduce((sum, r) => sum + r.workSeconds, 0))
const totalRest = computed(() => results.value.reduce((sum, r) => sum + r.restSeconds, 0))

function pad(n: number) { return String(n).padStart(2, '0') }
function formatHM(d: Date) { return `${pad(d.getHours())}:${pad(d.getMinutes())}` }
function formatClock(d: Date) { return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}` }
function formatTimer(totalSeconds: number) {
  const m = Math.floor(totalSeconds / 60)
  const s = Math.round(totalSeconds) % 60
  return `${m}:${pad(s)}`
}
function elapsedSincePhaseStart() {
  return Math.round((Date.now() - phaseStartedAt.value) / 1000)
}

function resetForNewExercise() {
  const ex = currentExercise.value
  const t = effectiveTarget(ex)
  currentSet.value = 1
  accumulatedWork.value = 0
  accumulatedRest.value = 0
  exerciseStartedAtClock.value = formatClock(new Date())
  entry.sets = t.sets ? String(t.sets) : '1'
  entry.reps = t.reps ? String(t.reps) : ''
  entry.weight = kgToDisplay(t.weightKg, weightUnit.value)?.toString() ?? ''
  entry.distance = kmToDisplay(t.distanceKm, distanceUnit.value)?.toString() ?? ''
}

function startWorkPhase(isNewExercise: boolean) {
  phase.value = 'work'
  phaseStartedAt.value = Date.now()
  if (isNewExercise) resetForNewExercise()
  else currentSet.value += 1
  saveState()
}

function startRestPhase() {
  accumulatedWork.value += elapsedSincePhaseStart()
  entry.sets = String(currentSet.value)
  phase.value = 'rest'
  phaseStartedAt.value = Date.now()
  saveState()
}

function goToNextSet() {
  accumulatedRest.value += elapsedSincePhaseStart()
  startWorkPhase(false)
}

function finishExerciseAndAdvance() {
  if (phase.value === 'rest') accumulatedRest.value += elapsedSincePhaseStart()
  else accumulatedWork.value += elapsedSincePhaseStart()
  entry.sets = entry.sets || String(currentSet.value)

  const ex = currentExercise.value
  results.value.push({
    name: ex.name,
    startedAt: exerciseStartedAtClock.value,
    workSeconds: accumulatedWork.value,
    restSeconds: accumulatedRest.value,
    sets: entry.sets,
    reps: entry.reps,
    weightKg: displayToKg(entry.weight, weightUnit.value),
    distanceKm: displayToKm(entry.distance, distanceUnit.value),
  })

  if (index.value < exercises.value.length - 1) {
    index.value += 1
    startWorkPhase(true)
  } else {
    phase.value = 'summary'
    saveState()
    releaseWakeLock()
  }
}

async function save() {
  saving.value = true
  try {
    const { sessionId } = await $fetch<{ sessionId: number }>(`/api/guided/${dayId}/finish`, {
      method: 'POST',
      body: { startTime: sessionStartClock.value, endTime: formatHM(new Date()), results: results.value },
    })
    clearSavedState()
    await navigateTo(`/history/${sessionId}`)
  } catch {
    saving.value = false
  }
}

// ---- Resume-after-refresh via localStorage ----
const storageKey = computed(() => `gymtrack_guided_${dayId}`)
const STALE_MS = 6 * 60 * 60 * 1000

function saveState() {
  try {
    localStorage.setItem(storageKey.value, JSON.stringify({
      index: index.value, phase: phase.value, currentSet: currentSet.value,
      accumulatedWork: accumulatedWork.value, accumulatedRest: accumulatedRest.value,
      results: results.value, sessionStartClock: sessionStartClock.value,
      exerciseStartedAtClock: exerciseStartedAtClock.value,
      elapsedAtSaveMs: Date.now() - phaseStartedAt.value,
      savedAt: Date.now(),
    }))
  } catch { /* localStorage unavailable -- degrade silently */ }
}
function clearSavedState() {
  try { localStorage.removeItem(storageKey.value) } catch { /* ignore */ }
}
function loadSavedState(): any {
  try {
    const raw = localStorage.getItem(storageKey.value)
    if (!raw) return null
    const saved = JSON.parse(raw)
    if (!saved || typeof saved.index !== 'number') return null
    if (Date.now() - (saved.savedAt || 0) > STALE_MS) return null
    if (saved.index >= exercises.value.length) return null
    return saved
  } catch { return null }
}
function restoreFromSaved(saved: any) {
  index.value = saved.index
  phase.value = saved.phase
  currentSet.value = saved.currentSet
  accumulatedWork.value = saved.accumulatedWork || 0
  accumulatedRest.value = saved.accumulatedRest || 0
  results.value = Array.isArray(saved.results) ? saved.results : []
  sessionStartClock.value = saved.sessionStartClock || sessionStartClock.value
  exerciseStartedAtClock.value = saved.exerciseStartedAtClock
  phaseStartedAt.value = Date.now() - (saved.elapsedAtSaveMs || 0)
  if (phase.value === 'work') {
    entry.sets = String(currentSet.value)
  }
}

function boot() {
  const saved = loadSavedState()
  if (saved && confirm('Looks like a workout got interrupted. Resume where you left off?')) {
    restoreFromSaved(saved)
  } else {
    if (saved) clearSavedState()
    startWorkPhase(true)
  }
}

// ---- Keep the screen awake while a workout is in progress ----
let wakeLock: any = null
async function requestWakeLock() {
  if (!('wakeLock' in navigator) || phase.value === 'summary') return
  try { wakeLock = await (navigator as any).wakeLock.request('screen') } catch { /* unsupported/denied */ }
}
function releaseWakeLock() {
  if (wakeLock) { wakeLock.release().catch(() => {}); wakeLock = null }
}
function onVisibilityChange() {
  if (document.visibilityState === 'visible' && phase.value !== 'summary') requestWakeLock()
}

let tickHandle: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  tickHandle = setInterval(() => { elapsedSeconds.value = elapsedSincePhaseStart() }, 250)
  document.addEventListener('visibilitychange', onVisibilityChange)
  requestWakeLock()
})
onUnmounted(() => {
  if (tickHandle) clearInterval(tickHandle)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  releaseWakeLock()
})
</script>
