<template>
  <div>
    <div v-if="pending" class="text-slate-400">Loading…</div>
    <template v-else-if="session">
      <div class="text-center mb-8">
        <span class="inline-flex text-fire mb-2"><Icon name="trophy" class="w-12 h-12" /></span>
        <h1 class="text-2xl font-bold">Your Journey</h1>
        <p class="text-sm text-slate-400">{{ session.dayName }} &middot; {{ formattedDate }}</p>
      </div>

      <div class="grid gap-3 mb-10" :style="{ gridTemplateColumns: `repeat(${chipCount}, minmax(0, 1fr))` }">
        <div v-if="session.startTime || session.endTime" class="card glow-border rounded-2xl p-3 text-center">
          <p class="text-lg font-bold text-accent">{{ sessionWindowLabel }}</p>
          <p class="text-[11px] text-slate-500">Session Window</p>
        </div>
        <template v-if="hasTimingData">
          <div class="card glow-border rounded-2xl p-3 text-center">
            <p class="text-lg font-bold text-accent2">{{ formatDuration(totalWork) }}</p>
            <p class="text-[11px] text-slate-500">Time Working</p>
          </div>
          <div class="card glow-border rounded-2xl p-3 text-center">
            <p class="text-lg font-bold text-fire">{{ formatDuration(totalRest) }}</p>
            <p class="text-[11px] text-slate-500">Time Resting</p>
          </div>
        </template>
        <div v-else class="card glow-border rounded-2xl p-3 text-center">
          <p class="text-lg font-bold text-accent2">{{ session.exercises.length }}</p>
          <p class="text-[11px] text-slate-500">Exercise{{ session.exercises.length !== 1 ? 's' : '' }} Logged</p>
        </div>
      </div>

      <div class="relative pl-8 mb-10">
        <div class="absolute left-3 top-2 bottom-2 w-0.5 bg-gradient-to-b from-accent via-accent2 to-fire" />

        <div
          v-for="(exercise, i) in session.exercises"
          :key="exercise.name"
          ref="timelineNodes"
          class="timeline-node relative mb-6 opacity-0 translate-y-4 transition-all duration-700 ease-out"
          :style="{ transitionDelay: `${i * 60}ms` }"
        >
          <span class="absolute -left-8 top-1 w-6 h-6 rounded-full bg-panel border-2 border-accent flex items-center justify-center text-accent">
            <Icon name="dumbbell" class="w-3.5 h-3.5" />
          </span>
          <div class="card glow-border rounded-2xl p-4">
            <div class="flex items-center justify-between mb-1.5">
              <span class="font-semibold">{{ exercise.name }}</span>
              <span v-if="exercise.startedAt" class="text-xs text-slate-500">{{ formatClockTime(exercise.startedAt) }}</span>
            </div>
            <div class="flex flex-wrap gap-1.5 text-xs">
              <span v-if="summaryFor(exercise).setsCount" class="px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300">
                {{ summaryFor(exercise).setsCount }} &times; {{ summaryFor(exercise).repsMax ?? '-' }}
              </span>
              <span v-if="summaryFor(exercise).weightDisplay != null" class="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300">
                {{ summaryFor(exercise).weightDisplay }} {{ weightUnit }}
              </span>
              <span v-if="summaryFor(exercise).distanceDisplay != null" class="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300">
                {{ summaryFor(exercise).distanceDisplay }} {{ distanceUnit }}
              </span>
              <span v-if="exercise.workSeconds" class="px-2 py-0.5 rounded-full bg-accent/10 text-accent flex items-center gap-1">
                {{ formatDuration(exercise.workSeconds) }}
              </span>
              <span v-if="exercise.restSeconds" class="px-2 py-0.5 rounded-full bg-fire/10 text-fire flex items-center gap-1">
                {{ formatDuration(exercise.restSeconds) }} rest
              </span>
            </div>
          </div>
        </div>

        <div ref="finishNode" class="timeline-node relative opacity-0 translate-y-4 transition-all duration-700 ease-out" :style="{ transitionDelay: `${session.exercises.length * 60}ms` }">
          <span class="absolute -left-8 top-1 w-6 h-6 rounded-full bg-fire flex items-center justify-center text-bg">
            <Icon name="check-circle" class="w-3.5 h-3.5" />
          </span>
          <div class="card glow-border rounded-2xl p-4 text-center">
            <p class="font-semibold">Finish line! Nicely done.</p>
          </div>
        </div>
      </div>

      <div class="flex gap-3">
        <NuxtLink to="/history" class="tap flex-1 py-3 rounded-lg bg-slate-700 text-center hover:bg-slate-600 transition">History</NuxtLink>
        <NuxtLink to="/dashboard" class="tap flex-1 py-3 rounded-lg bg-accent text-bg font-semibold text-center hover:shadow-glow transition">Dashboard</NuxtLink>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

interface SetRow { id: number; setNumber: number; reps: number | null; weightKg: number | null; distanceKm: number | null }
interface ExerciseGroup {
  name: string
  sets: SetRow[]
  startedAt: string | null
  workSeconds: number | null
  restSeconds: number | null
}
interface SessionDetail {
  id: number
  performedAt: string
  dayName: string
  startTime: string | null
  endTime: string | null
  exercises: ExerciseGroup[]
}

const { user } = useUserSession()
const weightUnit = computed(() => user.value?.weightUnit ?? 'kg')
const distanceUnit = computed(() => user.value?.distanceUnit ?? 'km')
const route = useRoute()
const { data: session, pending } = await useFetch<SessionDetail>(`/api/sessions/${route.params.id}`)

const formattedDate = computed(() => {
  if (!session.value) return ''
  return formatSessionDate(session.value.performedAt, { dateStyle: 'full' })
})

const hasTimingData = computed(() =>
  (session.value?.exercises ?? []).some((ex) => ex.workSeconds != null || ex.restSeconds != null),
)

const chipCount = computed(() => {
  if (!session.value) return 1
  const windowChip = session.value.startTime || session.value.endTime ? 1 : 0
  const timingChips = hasTimingData.value ? 2 : 1
  return windowChip + timingChips
})

const sessionWindowLabel = computed(() => {
  const s = session.value
  if (!s) return ''
  if (s.startTime && s.endTime) return `${formatClockTime(s.startTime)}\u2013${formatClockTime(s.endTime)}`
  if (s.startTime) return `Started ${formatClockTime(s.startTime)}`
  if (s.endTime) return `Ended ${formatClockTime(s.endTime)}`
  return ''
})

const totalWork = computed(() => (session.value?.exercises ?? []).reduce((sum, ex) => sum + (ex.workSeconds ?? 0), 0))
const totalRest = computed(() => (session.value?.exercises ?? []).reduce((sum, ex) => sum + (ex.restSeconds ?? 0), 0))

/**
 * One summary per exercise for this session, same aggregation rule used
 * by the progress charts (max weight, sum distance, max reps, count
 * sets) -- this schema logs individual sets, not one aggregate row like
 * the legacy app, so "the" number for a timeline pill needs a rule.
 */
function summaryFor(exercise: ExerciseGroup) {
  const sets = exercise.sets
  const weights = sets.map((s) => s.weightKg).filter((v): v is number => v != null)
  const distances = sets.map((s) => s.distanceKm).filter((v): v is number => v != null)
  const reps = sets.map((s) => s.reps).filter((v): v is number => v != null)
  return {
    setsCount: sets.length,
    repsMax: reps.length ? Math.max(...reps) : null,
    weightDisplay: weights.length ? kgToDisplay(Math.max(...weights), weightUnit.value) : null,
    distanceDisplay: distances.length ? kmToDisplay(distances.reduce((a, b) => a + b, 0), distanceUnit.value) : null,
  }
}

function formatClockTime(hhmm: string) {
  const [h, m] = hhmm.split(':').map(Number)
  const period = h < 12 ? 'AM' : 'PM'
  const h12 = h % 12 || 12
  return `${h12}:${String(m).padStart(2, '0')} ${period}`
}

function formatDuration(totalSeconds: number) {
  const s = Math.round(totalSeconds)
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${String(sec).padStart(2, '0')}`
}

// ---- Scroll-reveal for timeline nodes ----
const timelineNodes = ref<HTMLElement[]>([])
const finishNode = ref<HTMLElement | null>(null)
onMounted(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.remove('opacity-0', 'translate-y-4')
          observer.unobserve(entry.target)
        }
      }
    },
    { threshold: 0.15 },
  )
  for (const node of timelineNodes.value) observer.observe(node)
  if (finishNode.value) observer.observe(finishNode.value)
})
</script>
