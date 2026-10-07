<template>
  <NuxtLink
    :to="`/history/${session.id}`"
    class="tap card glow-border rounded-2xl flex items-center justify-between gap-3 px-5 py-4 hover:border-accent/60 transition"
  >
    <div class="min-w-0">
      <p class="font-semibold truncate">{{ formattedDate }}</p>
      <p class="text-xs text-slate-500">
        {{ session.dayName }} · {{ session.exerciseCount }} exercise{{ session.exerciseCount === 1 ? '' : 's' }}
      </p>
    </div>
    <span class="text-accent shrink-0 flex items-center gap-1 text-xs font-semibold">
      View <Icon name="chevron-down" class="w-4 h-4 -rotate-90" />
    </span>
  </NuxtLink>
</template>

<script setup lang="ts">
const props = defineProps<{
  session: { id: number; performedAt: string; dayName: string; exerciseCount: number }
}>()

const formattedDate = computed(() =>
  formatSessionDate(props.session.performedAt, { dateStyle: 'medium', timeStyle: 'short' }),
)
</script>
