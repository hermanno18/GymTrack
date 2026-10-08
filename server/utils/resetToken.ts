/**
 * Self-invalidating password-reset tokens, ported from the same design
 * in legacy-flask/app/auth.py: the token embeds a fingerprint of the
 * CURRENT password hash, so using it (or changing the password any
 * other way) automatically invalidates it for future reuse -- no
 * database table of issued/used tokens needed.
 *
 * Signed with HMAC-SHA256 using the same secret nuxt-auth-utils already
 * requires for session cookies (NUXT_SESSION_PASSWORD) -- one secret,
 * one place it's configured, no new env var to wire up on cPanel.
 */
import { createHmac, timingSafeEqual } from 'node:crypto'

const RESET_TOKEN_MAX_AGE_MS = 30 * 60 * 1000

function secret(): string {
  const value = process.env.NUXT_SESSION_PASSWORD
  if (!value) throw new Error('NUXT_SESSION_PASSWORD must be set')
  return value
}

/**
 * werkzeug-hash-slicing gotcha doesn't apply to bcrypt (every hash is a
 * fixed-length string with a per-call random salt baked in already),
 * but we still hash the whole thing rather than trust a raw substring
 * -- consistent with the legacy approach and marginally cheaper to
 * reason about than "which part of a bcrypt hash is safe to expose".
 */
function passwordFingerprint(passwordHash: string): string {
  return createHmac('sha256', secret()).update(passwordHash).digest('hex').slice(0, 16)
}

function base64url(input: string): string {
  return Buffer.from(input).toString('base64url')
}

export function makeResetToken(userId: number, passwordHash: string): string {
  const payload = {
    uid: userId,
    fp: passwordFingerprint(passwordHash),
    exp: Date.now() + RESET_TOKEN_MAX_AGE_MS,
  }
  const body = base64url(JSON.stringify(payload))
  const signature = createHmac('sha256', secret()).update(body).digest('hex')
  return `${body}.${signature}`
}

/** Returns the userId if the token is well-formed, unexpired, and the
 * password hasn't changed since it was issued. null otherwise. */
export function verifyResetToken(token: string, currentPasswordHash: string | null): number | null {
  const [body, signature] = token.split('.')
  if (!body || !signature) return null

  const expectedSignature = createHmac('sha256', secret()).update(body).digest('hex')
  const sigBuf = Buffer.from(signature, 'hex')
  const expectedBuf = Buffer.from(expectedSignature, 'hex')
  if (sigBuf.length !== expectedBuf.length || !timingSafeEqual(sigBuf, expectedBuf)) return null

  let payload: { uid: number; fp: string; exp: number }
  try {
    payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf-8'))
  } catch {
    return null
  }

  if (typeof payload.exp !== 'number' || Date.now() > payload.exp) return null
  if (!currentPasswordHash || passwordFingerprint(currentPasswordHash) !== payload.fp) return null

  return payload.uid
}
