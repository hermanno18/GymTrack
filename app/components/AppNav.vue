<template>
  <nav class="glow-border border-b bg-panel/70 backdrop-blur sticky top-0 z-20">
    <div class="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
      <NuxtLink to="/dashboard" class="text-xl font-bold tracking-wide text-accent flex items-center gap-2">
        <span class="flame-icon"><Icon name="flame" class="w-5 h-5" /></span>
        GYM<span class="text-accent2">TRACK</span>
      </NuxtLink>
      <div class="hidden md:flex items-center gap-5 text-sm">
        <NuxtLink to="/programs" class="hover:text-accent transition">Programs</NuxtLink>
        <button class="text-slate-400 hover:text-red-400 transition" @click="logout">Logout</button>
      </div>
      <div class="flex md:hidden items-center gap-4">
        <button class="text-slate-400" aria-label="Logout" @click="logout">
          <Icon name="power" class="w-5 h-5" />
        </button>
      </div>
    </div>
  </nav>

  <nav class="bottom-nav md:hidden fixed bottom-0 inset-x-0 z-20 bg-panel/95 backdrop-blur border-t border-cyan-500/20">
    <div class="grid grid-cols-3 text-center text-[10px] text-slate-400">
      <NuxtLink to="/dashboard" class="tap flex flex-col items-center py-2 gap-0.5 hover:text-accent">
        <Icon name="home" class="w-5 h-5" /><span>Home</span>
      </NuxtLink>
      <NuxtLink to="/programs" class="tap flex flex-col items-center -mt-5">
        <span class="w-14 h-14 rounded-full bg-gradient-to-br from-accent to-accent2 text-bg flex items-center justify-center shadow-glow pulse-cta">
          <Icon name="plus" class="w-7 h-7" />
        </span>
      </NuxtLink>
      <NuxtLink to="/programs" class="tap flex flex-col items-center py-2 gap-0.5 hover:text-accent">
        <Icon name="clipboard" class="w-5 h-5" /><span>Plans</span>
      </NuxtLink>
    </div>
  </nav>
</template>

<script setup lang="ts">
const { clear } = useUserSession()
const { confirm } = useConfirm()

async function logout() {
  if (!(await confirm('Log out of GymTrack?'))) return
  await clear()
  await navigateTo('/login')
}
</script>
