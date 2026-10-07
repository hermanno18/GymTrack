import bcrypt from 'bcryptjs'
import { eq } from 'drizzle-orm'
import { users } from '../../database/schema'
import { emailChangeSchema } from '../../utils/validation/settings'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const body = await readBody(event)
  const parsed = emailChangeSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }
  const { currentPassword, newEmail } = parsed.data

  const current = db.select().from(users).where(eq(users.id, user.id)).get()!
  if (!(await bcrypt.compare(currentPassword, current.passwordHash))) {
    throw createError({ statusCode: 401, statusMessage: 'Current password is incorrect' })
  }
  if (newEmail === current.email) {
    throw createError({ statusCode: 400, statusMessage: "That's already your email" })
  }
  const existing = db.select().from(users).where(eq(users.email, newEmail)).get()
  if (existing) {
    throw createError({ statusCode: 409, statusMessage: 'That email is already in use' })
  }

  const updated = db.update(users).set({ email: newEmail }).where(eq(users.id, user.id)).returning().get()
  await setUserSession(event, {
    user: { id: updated.id, email: updated.email, weightUnit: updated.weightUnit, distanceUnit: updated.distanceUnit },
  })

  return { ok: true }
})
