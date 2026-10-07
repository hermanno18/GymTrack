import bcrypt from 'bcryptjs'
import { eq } from 'drizzle-orm'
import { users } from '../../database/schema'
import { passwordChangeSchema } from '../../utils/validation/settings'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const body = await readBody(event)
  const parsed = passwordChangeSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }
  const { currentPassword, newPassword } = parsed.data

  const current = db.select().from(users).where(eq(users.id, user.id)).get()!
  if (!(await bcrypt.compare(currentPassword, current.passwordHash))) {
    throw createError({ statusCode: 401, statusMessage: 'Current password is incorrect' })
  }

  const passwordHash = await bcrypt.hash(newPassword, 12)
  db.update(users).set({ passwordHash }).where(eq(users.id, user.id)).run()

  return { ok: true }
})
