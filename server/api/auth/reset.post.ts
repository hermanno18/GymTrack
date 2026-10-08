import bcrypt from 'bcryptjs'
import { eq } from 'drizzle-orm'
import { users } from '../../database/schema'
import { resetPasswordSchema } from '../../utils/validation/auth'
import { verifyResetToken } from '../../utils/resetToken'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const parsed = resetPasswordSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }
  const { token, password } = parsed.data

  // Look up the token's claimed user first so we can check the fingerprint
  // against their CURRENT hash (that's what makes the token self-invalidating).
  const tokenPayload = token.split('.')[0]
  let claimedUserId: number | undefined
  try {
    claimedUserId = JSON.parse(Buffer.from(tokenPayload, 'base64url').toString('utf-8')).uid
  } catch {
    throw createError({ statusCode: 400, statusMessage: 'That reset link is invalid or has expired.' })
  }

  const user = claimedUserId ? db.select().from(users).where(eq(users.id, claimedUserId)).get() : undefined
  const userId = user ? verifyResetToken(token, user.passwordHash) : null
  if (!userId || !user) {
    throw createError({ statusCode: 400, statusMessage: 'That reset link is invalid or has expired.' })
  }

  const passwordHash = await bcrypt.hash(password, 12)
  db.update(users).set({ passwordHash }).where(eq(users.id, userId)).run()

  return { ok: true }
})
