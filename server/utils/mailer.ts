/**
 * Minimal outbound email for password-reset links, ported from
 * legacy-flask/app/mailer.py. Same fallback behavior: if SMTP_HOST
 * isn't configured (local dev, or before an admin sets up a mailbox),
 * the reset link is logged instead of emailed -- the forgot-password
 * flow still works end-to-end for local testing, it just logs the link.
 *
 * nodemailer is the Node equivalent of Python's stdlib smtplib used
 * there; same one-transactional-email-type scope, so no templating
 * engine or third-party email service needed.
 */
import nodemailer from 'nodemailer'

export async function sendPasswordResetEmail(toEmail: string, resetUrl: string): Promise<boolean> {
  const subject = 'Reset your GymTrack password'
  const body =
    'Someone (hopefully you) requested a password reset for GymTrack.\n\n' +
    `Reset your password here (link expires in 30 minutes):\n${resetUrl}\n\n` +
    "If you didn't request this, you can safely ignore this email -- " +
    "your password won't change unless you click the link above."

  return send(toEmail, subject, body)
}

async function send(toEmail: string, subject: string, body: string): Promise<boolean> {
  const host = process.env.SMTP_HOST
  if (!host) {
    console.warn(`[mailer] SMTP_HOST not configured -- would have emailed ${toEmail}:\n${body}`)
    return false
  }

  const port = Number(process.env.SMTP_PORT || '587')
  const username = process.env.SMTP_USERNAME
  const password = process.env.SMTP_PASSWORD
  const fromEmail = process.env.SMTP_FROM_EMAIL || username || 'noreply@gymtrack.local'
  const useSsl = ['1', 'true', 'yes'].includes((process.env.SMTP_USE_SSL || '').toLowerCase()) || port === 465

  try {
    const transporter = nodemailer.createTransport({
      host,
      port,
      secure: useSsl,
      auth: username && password ? { user: username, pass: password } : undefined,
      connectionTimeout: 10_000,
    })
    await transporter.sendMail({ from: fromEmail, to: toEmail, subject, text: body })
    return true
  } catch (err) {
    // A transient mail-server hiccup should never surface as a 500 to
    // the user -- the forgot-password route always shows the same
    // generic "a reset link is on its way" message regardless of
    // whether sending actually succeeded, so swallowing this here
    // (after logging it loudly) is the correct behavior, not
    // error-hiding.
    console.error(`[mailer] Failed to send password reset email to ${toEmail}:`, err)
    return false
  }
}
