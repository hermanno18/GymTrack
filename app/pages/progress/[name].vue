<template>
  <div class="space-y-6">
    <div v-if="pending" class="text-slate-400">Loading…</div>
    <div v-else-if="error" class="card glow-border rounded-2xl p-6 text-center text-slate-400 text-sm">
      No logged history for this exercise yet. Log a workout with it to start tracking progress.
    </div>
    <template v-else-if="data">
      <div>
        <h1 class="text-2xl font-bold flex items-center gap-2">
          <Icon name="chart" class="w-6 h-6 text-accent" /> {{ data.displayName }}
        </h1>
        <p class="text-sm text-slate-400 mt-1">Tap a metric to switch what the chart tracks.</p>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          v-for="metric in availableMetrics"
          :key="metric.key"
          type="button"
          class="tap text-sm px-4 py-2 rounded-full border transition"
          :class="activeMetric === metric.key ? 'bg-accent text-bg border-accent' : 'border-slate-700 text-slate-300 hover:border-accent'"
          @click="activeMetric = metric.key"
        >
          {{ metric.label }}
        </button>
      </div>

      <div class="card glow-border rounded-2xl p-6">
        <div class="h-80">
          <canvas ref="canvasRef" />
        </div>
      </div>

      <div class="card glow-border rounded-2xl p-6 overflow-x-auto">
        <h2 class="font-semibold text-accent mb-4">Log History</h2>
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-slate-500 border-b border-slate-700">
              <th class="py-2">Date</th>
              <th>Sets</th>
              <th>Best Reps</th>
              <th>Best Weight ({{ weightUnit }})</th>
              <th>Total Distance ({{ distanceUnit }})</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in data.history" :key="row.performedAt" class="border-b border-slate-800">
              <td class="py-2">{{ formatSessionDate(row.performedAt, { dateStyle: 'medium' }) }}</td>
              <td>{{ row.setsCount }}</td>
              <td>{{ row.repsMax ?? '-' }}</td>
              <td>{{ kgToDisplay(row.weightMax, weightUnit) ?? '-' }}</td>
              <td>{{ kmToDisplay(row.distanceSum, distanceUnit) ?? '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Chart, registerables } from 'chart.js'

definePageMeta({ middleware: 'auth', layout: 'app' })
Chart.register(...registerables)

interface SeriesPoint { date: string; value: number }
interface Series { label: string; points: SeriesPoint[] }
interface ProgressData {
  displayName: string
  series: Record<'weight' | 'distance' | 'reps' | 'sets', Series | null>
  history: { performedAt: string; weightMax: number | null; distanceSum: number | null; repsMax: number | null; setsCount: number }[]
}

const route = useRoute()
const { user } = useUserSession()
const weightUnit = computed(() => user.value?.weightUnit ?? 'kg')
const distanceUnit = computed(() => user.value?.distanceUnit ?? 'km')

const { data, pending, error } = await useFetch<ProgressData>(`/api/progress/${route.params.name}`)

const metricMeta = {
  weight: { key: 'weight' as const, label: computed(() => `Weight (${weightUnit.value})`) },
  distance: { key: 'distance' as const, label: computed(() => `Distance (${distanceUnit.value})`) },
  reps: { key: 'reps' as const, label: 'Best Reps' },
  sets: { key: 'sets' as const, label: 'Sets' },
}

const availableMetrics = computed(() =>
  (Object.keys(metricMeta) as Array<keyof typeof metricMeta>)
    .filter((key) => data.value?.series[key])
    .map((key) => ({ key, label: unref(metricMeta[key].label) })),
)

const activeMetric = ref<keyof typeof metricMeta | null>(null)
watchEffect(() => {
  if (!activeMetric.value && availableMetrics.value.length) {
    activeMetric.value = availableMetrics.value[0].key
  }
})

function displayValue(metric: keyof typeof metricMeta, raw: number) {
  if (metric === 'weight') return kgToDisplay(raw, weightUnit.value)
  if (metric === 'distance') return kmToDisplay(raw, distanceUnit.value)
  return raw
}

const canvasRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

function renderChart() {
  const metric = activeMetric.value
  const series = metric ? data.value?.series[metric] : null
  if (!canvasRef.value || !series || !metric) return

  chart?.destroy()
  chart = new Chart(canvasRef.value, {
    type: 'line',
    data: {
      labels: series.points.map((p) => formatSessionDate(p.date, { month: 'short', day: 'numeric' })),
      datasets: [{
        label: unref(metricMeta[metric].label),
        data: series.points.map((p) => displayValue(metric, p.value)),
        borderColor: '#22d3ee',
        backgroundColor: 'rgba(34, 211, 238, 0.15)',
        tension: 0.3,
        fill: true,
        pointBackgroundColor: '#a855f7',
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
      },
      plugins: {
        legend: { labels: { color: '#e2e8f0' } },
      },
    },
  })
}

watch([activeMetric, canvasRef], renderChart)
onMounted(renderChart)
onUnmounted(() => chart?.destroy())
</script>
