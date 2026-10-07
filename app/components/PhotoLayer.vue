<template>
  <div
    class="bg-cover bg-center pointer-events-none"
    :class="[extraClasses, opacity]"
    :style="{ backgroundImage: `url(/images/${filename})` }"
  />
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{ filename: string; opacity?: string; extraClasses?: string }>(),
  { opacity: 'opacity-30', extraClasses: 'absolute inset-0' },
)
</script>
