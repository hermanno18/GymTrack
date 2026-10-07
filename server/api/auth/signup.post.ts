import bcrypt from 'bcryptjs'
import { eq } from 'drizzle-orm'
import { users } from '../../database/schema'
import { signupSchema } from '../../utils/validation/auth'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const parsed = signupSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }
  const { email, password } = parsed.data

  const existing = db.select().from(users).where(eq(users.email, email)).get()
  if (existing) {
    throw createError({ statusCode: 409, statusMessage: 'An account with that email already exists' })
  }

  const passwordHash = await bcrypt.hash(password, 12)
  const created = db.insert(users).values({ email, passwordHash }).returning().get()

  await setUserSession(event, {
    user: { id: created.id, email: created.email },
  })

  return { ok: true }
})
