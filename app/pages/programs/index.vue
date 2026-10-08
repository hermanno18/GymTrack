<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold flex items-center gap-2">
        <Icon name="clipboard" class="w-6 h-6 text-accent" /> Your Programs
      </h1>
      <NuxtLink to="/programs/upload" class="tap text-sm text-accent2 flex items-center gap-1 hover:underline">
        <Icon name="upload" class="w-4 h-4" /> Upload PDF
      </NuxtLink>
    </div>

    <form class="flex gap-2 mb-6" @submit.prevent="createProgram">
      <input
        v-model="newProgramName"
        type="text"
        placeholder="e.g. Push Pull Legs"
        required
        class="flex-1 rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent focus:outline-none transition"
      >
      <button
        type="submit"
        :disabled="creating"
        class="tap px-4 py-2.5 rounded-lg bg-accent text-bg font-semibold hover:shadow-glow disabled:opacity-50 transition"
      >
        {{ creating ? 'Adding…' : '+ New' }}
      </button>
    </form>

    <Transition name="fade">
      <p v-if="errorMessage" class="text-sm text-red-400 mb-4">{{ errorMessage }}</p>
    </Transition>

    <div v-if="pending" class="text-slate-400 text-sm">Loading…</div>

    <div v-else-if="programs?.length" class="grid md:grid-cols-2 gap-4">
      <TransitionGroup name="list">
        <div
          v-for="program in programs"
          :key="program.id"
          class="card glow-border rounded-2xl p-5 flex flex-col justify-between"
        >
          <div>
            <h2 class="font-semibold text-lg">{{ program.name }}</h2>
          </div>
          <div class="flex gap-4 mt-4 text-sm items-center">
            <NuxtLink :to="`/programs/${program.id}`" class="tap text-accent flex items-center gap-1">
              <Icon name="edit" class="w-4 h-4" /> Edit
            </NuxtLink>
            <button class="tap text-red-400 flex items-center gap-1" @click="deleteProgram(program.id)">
              <Icon name="trash" class="w-4 h-4" /> Delete
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <div v-else class="relative overflow-hidden rounded-2xl card glow-border p-8 text-center">
      <PhotoLayer filename="empty-programs.jpg" opacity="opacity-20" />
      <div class="absolute inset-0 bg-gradient-to-b from-transparent to-bg/80" />
      <div class="relative">
        <p class="text-slate-300 font-medium mb-1">No programs yet</p>
        <p class="text-slate-400 text-sm">Create one above to get moving.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

const { data: programs, pending, refresh } = await useFetch('/api/programs')
const newProgramName = ref('')
const creating = ref(false)
const errorMessage = ref('')
const { confirm } = useConfirm()

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

async function deleteProgram(id: number) {
  if (!(await confirm('Delete this program and all its exercises?'))) return
  await $fetch(`/api/programs/${id}`, { method: 'DELETE' })
  await refresh()
}
</script>
