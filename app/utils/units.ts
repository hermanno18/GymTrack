/**
 * Everything is stored internally in kg / km. Conversion only happens at
 * the display/input boundary so switching a user's preferred unit never
 * mutates historical data. Mirrors legacy-flask/app/utils.py exactly.
 */
export const KG_PER_LB = 0.45359237
export const KM_PER_MI = 1.609344

export type WeightUnit = 'kg' | 'lb'
export type DistanceUnit = 'km' | 'mi'

export function kgToDisplay(kg: number | null, unit: WeightUnit): number | null {
  if (kg === null) return null
  return unit === 'kg' ? round2(kg) : round2(kg / KG_PER_LB)
}

export function displayToKg(value: number | string | null, unit: WeightUnit): number | null {
  if (value === null || value === '') return null
  const num = Number(value)
  return unit === 'kg' ? num : round3(num * KG_PER_LB)
}

export function kmToDisplay(km: number | null, unit: DistanceUnit): number | null {
  if (km === null) return null
  return unit === 'km' ? round2(km) : round2(km / KM_PER_MI)
}

export function displayToKm(value: number | string | null, unit: DistanceUnit): number | null {
  if (value === null || value === '') return null
  const num = Number(value)
  return unit === 'km' ? num : round3(num * KM_PER_MI)
}

function round2(n: number) {
  return Math.round(n * 100) / 100
}
function round3(n: number) {
  return Math.round(n * 1000) / 1000
}
