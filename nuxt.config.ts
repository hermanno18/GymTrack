// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2026-10-07',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss', 'nuxt-auth-utils'],
  css: ['~/assets/css/main.css'],
})
