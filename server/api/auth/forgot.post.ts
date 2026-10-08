import { eq } from 'drizzle-orm'
import { users } from '../../database/schema'
import { forgotPasswordSchema } from '../../utils/validation/auth'
import { makeResetToken } from '../../utils/resetToken'
import { sendPasswordResetEmail } from '../../utils/mailer'

/**
 * Always returns the same generic response whether or not the email is
 * registered -- never let this endpoint be used to probe which emails
 * have accounts (mirrors legacy-flask/app/auth.py's forgot_password).
 */
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const parsed = forgotPasswordSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }

  const user = db.select().from(users).where(eq(users.email, parsed.data.email)).get()
  if (user) {
    const token = makeResetToken(user.id, user.passwordHash)
    const resetUrl = `${getRequestURL(event).origin}/reset-password/${token}`
    await sendPasswordResetEmail(user.email, resetUrl)
  }

  return { ok: true }
})
