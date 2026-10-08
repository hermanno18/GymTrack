<template>
  <div class="max-w-md">
    <h1 class="text-2xl font-bold mb-2 flex items-center gap-2">
      <Icon name="clipboard" class="w-6 h-6 text-accent" /> Upload a Program PDF
    </h1>
    <p class="text-sm text-slate-400 mb-6">
      We'll try to auto-extract your Days and exercises. You'll always get a chance to review and fix
      anything in the builder afterwards.
    </p>

    <Transition name="fade">
      <p v-if="errorMessage" class="text-sm text-red-400 mb-4">{{ errorMessage }}</p>
    </Transition>

    <form class="card glow-border rounded-2xl p-6 space-y-4" @submit.prevent="upload">
      <div>
        <label class="block text-sm text-slate-400 mb-1">Program name (optional)</label>
        <input
          v-model="name"
          type="text"
          placeholder="e.g. Coach Mike - Fall Block"
          class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2 focus:border-accent focus:outline-none transition"
        >
      </div>
      <div>
        <label class="block text-sm text-slate-400 mb-1">PDF file</label>
        <input
          ref="fileInput"
          type="file"
          accept="application/pdf"
          required
          class="w-full text-sm text-slate-300"
        >
      </div>
      <button
        type="submit"
        :disabled="uploading"
        class="tap w-full py-3 rounded-lg bg-accent text-bg font-semibold hover:shadow-glow transition disabled:opacity-50"
      >
        {{ uploading ? 'Uploading…' : 'Upload & Extract' }}
      </button>
    </form>

    <p class="text-sm text-slate-500 mt-4">
      No PDF, or extraction not cooperating?
      <NuxtLink to="/programs" class="text-accent hover:underline">Build one manually instead</NuxtLink>.
    </p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

const name = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const errorMessage = ref('')

async function upload() {
  const file = fileInput.value?.files?.[0]
  if (!file) {
    errorMessage.value = 'Please choose a PDF file to upload.'
    return
  }

  uploading.value = true
  errorMessage.value = ''
  try {
    const formData = new FormData()
    formData.append('pdf', file)
    if (name.value.trim()) formData.append('name', name.value.trim())

    const result = await $fetch<{ programId: number; parsed: boolean; exerciseCount: number }>(
      '/api/programs/upload-pdf',
      { method: 'POST', body: formData },
    )

    const message = result.parsed
      ? `Program imported! Found ${result.exerciseCount} exercise${result.exerciseCount !== 1 ? 's' : ''} -- review them below.`
      : "Couldn't automatically read exercises from that PDF. No worries -- add your days and exercises manually below."
    await navigateTo({ path: `/programs/${result.programId}`, query: { imported: message } })
  } catch (err: any) {
    errorMessage.value = err?.data?.statusMessage || 'Could not upload that file'
  } finally {
    uploading.value = false
  }
}
</script>
