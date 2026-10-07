<template>
  <div class="min-h-screen bg-slate-950 text-white">
    <AppNav />
    <main class="max-w-3xl mx-auto px-6 py-10 space-y-8">
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold">Your programs</h1>
      </div>

      <form class="flex gap-2" @submit.prevent="createProgram">
        <input
          v-model="newProgramName"
          type="text"
          placeholder="e.g. Push Pull Legs"
          required
          class="flex-1 rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
        >
        <button
          type="submit"
          :disabled="creating"
          class="px-4 py-2 rounded-md bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold transition"
        >
          {{ creating ? 'Adding…' : 'New program' }}
        </button>
      </form>

      <p v-if="errorMessage" class="text-sm text-red-400">{{ errorMessage }}</p>

      <div v-if="pending" class="text-slate-400">Loading…</div>
      <div v-else-if="!programs?.length" class="text-slate-400">
        No programs yet. Create one above to get started.
      </div>
      <ul v-else class="space-y-2">
        <li v-for="program in programs" :key="program.id">
          <NuxtLink
            :to="`/programs/${program.id}`"
            class="block rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500 px-4 py-3 transition"
          >
            {{ program.name }}
          </NuxtLink>
        </li>
      </ul>
    </main>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { data: programs, pending, refresh } = await useFetch('/api/programs')
const newProgramName = ref('')
const creating = ref(false)
const errorMessage = ref('')

async function createProgram() {
  creating.value = true
  errorMessage.value = ''
  try {
    await $fetch('/api/programs', { method: 'POST', body: { name: newProgramName.value } })
    newProgramName.value = ''
    await refresh()
  } catch (err: any) {
    errorMessage.value = err?.data?.statusMessage || 'Could not create program'
  } finally {
    creating.value = false
  }
}
</script>
