/**
 * Best-effort parser for coach PDFs, ported line-for-line from
 * legacy-flask/app/pdf_parser.py (see that file's docstring for the
 * full rationale on why it looks for these two specific structural
 * patterns instead of treating every line as a candidate exercise).
 *
 * Deliberately NOT "improved" during the port -- e.g. the quantity-line
 * unit check below only recognizes "minutes"/"seconds" (plural), not the
 * singular "minute"/"second", exactly like the original. That's an
 * inherited quirk, not a new bug; fix it in both places at once if it
 * ever matters.
 */

export interface ParsedExercise {
  name: string
  sets: number | null
  reps: number | null
  weightKg: number | null
  distanceKm: number | null
  notes: string | null
}

export interface ParsedDay {
  label: string
  exercises: ParsedExercise[]
}

const DAY_HEADER_RE = /^[ \t]*day[ \t]*(\d+)[ \t]*[:\-\u2013\u2014]?[ \t]*(.*)$/i
const SUBSECTION_RE = /^[ \t]*\d+\.[ \t]*(.*)$/
const BULLET_RE = /^[ \t]*[\u25cf\u2022*\-][ \t]*/
const SETS_REPS_LINE_RE =
  /^[ \t]*(\d+)[ \t]*[x\u00d7][ \t]*(\d+(?:[\u2013\-]\d+)?)[ \t]*(seconds?|secs?|minutes?|mins?)?[ \t]*(each[ \t]+(side|leg|arm))?[ \t]*$/i
const QUANTITY_NAME_LINE_RE =
  /^[ \t]*(\d+(?:[\u2013\-]\d+)?)\s+(?:(m|km|meters?|min|mins?|minutes?|sec|secs?|seconds?)\s+)?([A-Za-z][A-Za-z'\- ]*)$/i
const CIRCUIT_SECTION_HINT_RE = /conditioning|circuit|round/i

export function parseProgramText(rawText: string): ParsedDay[] {
  const text = (rawText || '').replace(/\r\n/g, '\n')
  const lines = text.split('\n')

  const dayStarts: { lineNo: number; dayNum: string; title: string }[] = []
  lines.forEach((line, i) => {
    const m = line.match(DAY_HEADER_RE)
    if (m) dayStarts.push({ lineNo: i, dayNum: m[1], title: m[2].trim() })
  })
  if (!dayStarts.length) return []

  const days: ParsedDay[] = []
  dayStarts.forEach((start, idx) => {
    let label = `Day ${start.dayNum}`
    if (start.title) label += ` - ${start.title}`
    const endLine = idx + 1 < dayStarts.length ? dayStarts[idx + 1].lineNo : lines.length
    const dayLines = lines.slice(start.lineNo + 1, endLine)
    const exercises = parseDayLines(dayLines)
    if (exercises.length) days.push({ label, exercises })
  })
  return days
}

function parseDayLines(dayLines: string[]): ParsedExercise[] {
  const exercises: ParsedExercise[] = []
  const consumed = new Set<number>()
  extractNamePlusTargetPairs(dayLines, consumed, exercises)
  extractCircuitQuantityLines(dayLines, consumed, exercises)
  return exercises
}

function extractNamePlusTargetPairs(dayLines: string[], consumed: Set<number>, exercises: ParsedExercise[]) {
  for (let i = 0; i < dayLines.length - 1; i++) {
    if (consumed.has(i) || consumed.has(i + 1)) continue
    const nameLine = dayLines[i].trim()
    const targetLine = dayLines[i + 1].trim()
    if (!nameLine || BULLET_RE.test(nameLine) || SUBSECTION_RE.test(nameLine)) continue
    const targetMatch = targetLine.match(SETS_REPS_LINE_RE)
    if (!targetMatch) continue

    exercises.push(buildExerciseFromPair(nameLine, targetMatch))
    consumed.add(i)
    consumed.add(i + 1)
  }
}

function buildExerciseFromPair(nameLine: string, match: RegExpMatchArray): ParsedExercise {
  const sets = parseInt(match[1], 10)
  const repsRaw = match[2]
  const unit = match[3]
  const side = match[5]

  let reps: number | null = null
  const notesParts: string[] = []
  if (unit) {
    notesParts.push(`${repsRaw} ${unit}`)
  } else {
    reps = parseInt(repsRaw.split(/[\u2013\-]/)[0], 10)
  }
  if (side) notesParts.push(`each ${side}`)

  return {
    name: nameLine,
    sets,
    reps,
    weightKg: null,
    distanceKm: null,
    notes: notesParts.length ? notesParts.join('; ') : null,
  }
}

function extractCircuitQuantityLines(dayLines: string[], consumed: Set<number>, exercises: ParsedExercise[]) {
  let inCircuitSection = false
  dayLines.forEach((rawLine, i) => {
    const line = rawLine.trim()
    if (!line) return

    const subsection = line.match(SUBSECTION_RE)
    if (subsection) {
      inCircuitSection = CIRCUIT_SECTION_HINT_RE.test(subsection[1])
      return
    }

    if (consumed.has(i) || !inCircuitSection || BULLET_RE.test(line)) return
    const quantityMatch = line.match(QUANTITY_NAME_LINE_RE)
    if (!quantityMatch) return

    exercises.push(buildExerciseFromQuantityLine(quantityMatch))
    consumed.add(i)
  })
}

function buildExerciseFromQuantityLine(match: RegExpMatchArray): ParsedExercise {
  const quantityRaw = match[1]
  const name = match[3].trim()
  const firstNumber = parseFloat(quantityRaw.split(/[\u2013\-]/)[0])
  const unit = (match[2] || '').toLowerCase()

  let reps: number | null = null
  let distanceKm: number | null = null
  let notes: string | null = null
  if (['m', 'meters', 'meter'].includes(unit)) {
    distanceKm = Math.round((firstNumber / 1000) * 10000) / 10000
  } else if (unit === 'km') {
    distanceKm = firstNumber
  } else if (['min', 'mins', 'minutes', 'sec', 'secs', 'seconds'].includes(unit)) {
    notes = `${quantityRaw} ${unit}`
  } else {
    reps = Math.round(firstNumber)
  }

  return { name, sets: null, reps, weightKg: null, distanceKm, notes }
}
