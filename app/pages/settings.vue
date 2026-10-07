<template>
  <div class="max-w-lg space-y-6">
    <h1 class="text-2xl font-bold flex items-center gap-2">
      <Icon name="settings" class="w-6 h-6 text-accent" /> Settings
    </h1>

    <form class="card glow-border rounded-2xl p-6 space-y-4" @submit.prevent="saveUnits">
      <h2 class="font-semibold text-accent">Units</h2>
      <Transition name="fade">
        <p v-if="unitsMessage" class="text-sm" :class="unitsError ? 'text-red-400' : 'text-green-400'">{{ unitsMessage }}</p>
      </Transition>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-xs text-slate-400 mb-1">Weight</label>
          <select v-model="weightUnit" class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent focus:outline-none transition">
            <option value="kg">Kilograms (kg)</option>
            <option value="lb">Pounds (lb)</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">Distance</label>
          <select v-model="distanceUnit" class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent focus:outline-none transition">
            <option value="km">Kilometers (km)</option>
            <option value="mi">Miles (mi)</option>
          </select>
        </div>
      </div>
      <button type="submit" class="tap px-4 py-2.5 rounded-lg bg-accent text-bg font-semibold hover:shadow-glow transition">Save Units</button>
    </form>

    <form class="card glow-border rounded-2xl p-6 space-y-4" @submit.prevent="saveEmail">
      <h2 class="font-semibold text-accent2 flex items-center gap-2"><Icon name="mail" class="w-4 h-4" /> Change Email</h2>
      <Transition name="fade">
        <p v-if="emailMessage" class="text-sm" :class="emailError ? 'text-red-400' : 'text-green-400'">{{ emailMessage }}</p>
      </Transition>
      <p class="text-xs text-slate-500">Current: {{ user?.email }}</p>
      <input v-model="emailForm.currentPassword" type="password" placeholder="Current password" required class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent2 focus:outline-none transition">
      <input v-model="emailForm.newEmail" type="email" placeholder="New email" required class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent2 focus:outline-none transition">
      <button type="submit" class="tap px-4 py-2.5 rounded-lg bg-accent2 text-white font-semibold hover:shadow-glow transition">Update Email</button>
    </form>

    <form class="card glow-border rounded-2xl p-6 space-y-4" @submit.prevent="savePassword">
      <h2 class="font-semibold text-accent2 flex items-center gap-2"><Icon name="lock" class="w-4 h-4" /> Change Password</h2>
      <Transition name="fade">
        <p v-if="passwordMessage" class="text-sm" :class="passwordError ? 'text-red-400' : 'text-green-400'">{{ passwordMessage }}</p>
      </Transition>
      <input v-model="passwordForm.currentPassword" type="password" placeholder="Current password" required class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent2 focus:outline-none transition">
      <input v-model="passwordForm.newPassword" type="password" placeholder="New password" minlength="8" required class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent2 focus:outline-none transition">
      <input v-model="passwordForm.confirmPassword" type="password" placeholder="Confirm new password" minlength="8" required class="w-full rounded-lg bg-bg border border-slate-700 px-3 py-2.5 focus:border-accent2 focus:outline-none transition">
      <button type="submit" class="tap px-4 py-2.5 rounded-lg bg-accent2 text-white font-semibold hover:shadow-glow transition">Update Password</button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'app' })

const { user, fetch: refreshSession } = useUserSession()

const weightUnit = ref(user.value?.weightUnit ?? 'kg')
const distanceUnit = ref(user.value?.distanceUnit ?? 'km')
const unitsMessage = ref('')
const unitsError = ref(false)

async function saveUnits() {
  unitsMessage.value = ''
  try {
    await $fetch('/api/settings/units', { method: 'PATCH', body: { weightUnit: weightUnit.value, distanceUnit: distanceUnit.value } })
    await refreshSession()
    unitsError.value = false
    unitsMessage.value = 'Settings saved.'
  } catch (err: any) {
    unitsError.value = true
    unitsMessage.value = err?.data?.statusMessage || 'Could not save settings'
  }
}

const emailForm = reactive({ currentPassword: '', newEmail: '' })
const emailMessage = ref('')
const emailError = ref(false)

async function saveEmail() {
  emailMessage.value = ''
  try {
    await $fetch('/api/settings/email', { method: 'PATCH', body: emailForm })
    await refreshSession()
    emailError.value = false
    emailMessage.value = 'Email updated.'
    emailForm.currentPassword = ''
    emailForm.newEmail = ''
  } catch (err: any) {
    emailError.value = true
    emailMessage.value = err?.data?.statusMessage || 'Could not update email'
  }
}

const passwordForm = reactive({ currentPassword: '', newPassword: '', confirmPassword: '' })
const passwordMessage = ref('')
const passwordError = ref(false)

async function savePassword() {
  passwordMessage.value = ''
  try {
    await $fetch('/api/settings/password', { method: 'PATCH', body: passwordForm })
    passwordError.value = false
    passwordMessage.value = 'Password updated.'
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (err: any) {
    passwordError.value = true
    passwordMessage.value = err?.data?.statusMessage || 'Could not update password'
  }
}
</script>
