import bcrypt from 'bcryptjs'
import { eq } from 'drizzle-orm'
import { users } from '../../database/schema'
import { loginSchema } from '../../utils/validation/auth'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const parsed = loginSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }
  const { email, password } = parsed.data

  const user = db.select().from(users).where(eq(users.email, email)).get()
  if (!user) {
    throw createError({ statusCode: 401, statusMessage: 'Invalid email or password' })
  }

  const valid = await bcrypt.compare(password, user.passwordHash)
  if (!valid) {
    throw createError({ statusCode: 401, statusMessage: 'Invalid email or password' })
  }

  await setUserSession(event, {
    user: { id: user.id, email: user.email },
  })

  return { ok: true }
})
