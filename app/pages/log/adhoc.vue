<template>
  <div>
    <h1 class="text-2xl font-bold mb-6 flex items-center gap-2">
      <Icon name="dumbbell" class="w-6 h-6 text-accent" /> Free-form Session
    </h1>
    <LogSessionForm :day-id="null" />
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })
</script>
