import { eq } from 'drizzle-orm'
import { users } from '../../database/schema'
import { unitsSchema } from '../../utils/validation/settings'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)
  const body = await readBody(event)
  const parsed = unitsSchema.safeParse(body)
  if (!parsed.success) {
    throw createError({ statusCode: 400, statusMessage: parsed.error.issues[0].message })
  }

  const updated = db
    .update(users)
    .set({ weightUnit: parsed.data.weightUnit, distanceUnit: parsed.data.distanceUnit })
    .where(eq(users.id, user.id))
    .returning()
    .get()

  // Refresh the session cookie too, since the unit prefs live there for
  // fast client-side access without a round trip on every page.
  await setUserSession(event, {
    user: { id: updated.id, email: updated.email, weightUnit: updated.weightUnit, distanceUnit: updated.distanceUnit },
  })

  return { ok: true }
})
