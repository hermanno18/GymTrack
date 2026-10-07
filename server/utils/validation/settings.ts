import { z } from 'zod'

export const unitsSchema = z.object({
  weightUnit: z.enum(['kg', 'lb']),
  distanceUnit: z.enum(['km', 'mi']),
})

export const emailChangeSchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required'),
  newEmail: z.string().trim().toLowerCase().email('Enter a valid email address'),
})

export const passwordChangeSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z.string().min(8, 'New password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "New passwords don't match",
    path: ['confirmPassword'],
  })
