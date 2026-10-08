import { extractText, getDocumentProxy } from 'unpdf'
import { programs, programDays, exercises } from '../../database/schema'
import { parseProgramText } from '../../utils/pdfParser'

/**
 * Upload a coach's PDF, best-effort extract Days/Exercises from it.
 * Mirrors legacy-flask/app/programs.py's new_upload route:
 *   - Can't even read the file as a PDF -> reject, no program created.
 *   - Readable but nothing structured found -> still create an EMPTY
 *     program (never a dead end -- user finishes it in the builder).
 *   - Parsed successfully -> create the program with its days/exercises,
 *     still meant to be reviewed/edited in the builder afterwards.
 *
 * Not storing the raw extracted text or original filename (legacy did,
 * for debugging) -- nothing in this rewrite's UI surfaces either, so
 * skipping that column pair entirely rather than adding dead storage.
 */
export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)

  const parts = await readMultipartFormData(event)
  if (!parts) {
    throw createError({ statusCode: 400, statusMessage: 'Please choose a PDF file to upload.' })
  }
  const filePart = parts.find((p) => p.name === 'pdf' && p.filename)
  const namePart = parts.find((p) => p.name === 'name')

  if (!filePart || !filePart.filename) {
    throw createError({ statusCode: 400, statusMessage: 'Please choose a PDF file to upload.' })
  }
  if (!filePart.filename.toLowerCase().endsWith('.pdf')) {
    throw createError({ statusCode: 400, statusMessage: 'Only PDF files are supported.' })
  }

  let rawText: string
  try {
    const pdf = await getDocumentProxy(new Uint8Array(filePart.data))
    const result = await extractText(pdf, { mergePages: true })
    rawText = Array.isArray(result.text) ? result.text.join('\n') : result.text
  } catch {
    throw createError({
      statusCode: 422,
      statusMessage:
        "That file couldn't be read as a PDF (it may be scanned/image-only or corrupted). You can still build your program manually.",
    })
  }

  const baseName = filePart.filename.replace(/\.pdf$/i, '')
  const name = (namePart?.data.toString('utf-8').trim() || baseName || 'My Program').slice(0, 255)

  const program = db.insert(programs).values({ userId: user.id, name }).returning().get()

  const parsedDays = parseProgramText(rawText)
  for (let dayIndex = 0; dayIndex < parsedDays.length; dayIndex++) {
    const parsedDay = parsedDays[dayIndex]
    const day = db
      .insert(programDays)
      .values({ programId: program.id, name: parsedDay.label, position: dayIndex })
      .returning()
      .get()

    const exerciseRows = parsedDay.exercises.map((ex, exIndex) => ({
      programDayId: day.id,
      name: ex.name,
      position: exIndex,
      targetSets: ex.sets,
      targetReps: ex.reps,
      targetWeightKg: ex.weightKg,
      targetDistanceKm: ex.distanceKm,
    }))
    if (exerciseRows.length) {
      db.insert(exercises).values(exerciseRows).run()
    }
  }

  const exerciseCount = parsedDays.reduce((sum, d) => sum + d.exercises.length, 0)
  return { programId: program.id, parsed: parsedDays.length > 0, dayCount: parsedDays.length, exerciseCount }
})
