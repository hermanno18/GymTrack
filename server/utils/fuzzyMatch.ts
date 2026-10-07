/**
 * Fuzzy "did you mean X?" matching for exercise names, so the same lift
 * logged under slightly different spellings/casing still links up for
 * progression tracking. Mirrors legacy-flask/app/utils.py's
 * normalize_name + find_similar_exercise, with one deliberate swap:
 * Python's difflib.SequenceMatcher isn't available in JS, so this uses
 * Dice's (bigram) coefficient instead -- a different algorithm, but the
 * same "0..1 similarity score, tune the threshold" shape. 0.85 remains a
 * sensible "pretty clearly the same exercise" cutoff for either.
 */
export function normalizeName(name: string): string {
  return (name ?? '').trim().toLowerCase().replace(/\s+/g, ' ')
}

function bigrams(s: string): string[] {
  const grams: string[] = []
  for (let i = 0; i < s.length - 1; i++) grams.push(s.slice(i, i + 2))
  return grams
}

export function similarityRatio(a: string, b: string): number {
  if (a === b) return 1
  if (a.length < 2 || b.length < 2) return 0
  const gramsA = bigrams(a)
  const gramsBOriginalLength = bigrams(b).length
  const gramsBRemaining = bigrams(b)
  let matches = 0
  for (const gram of gramsA) {
    const idx = gramsBRemaining.indexOf(gram)
    if (idx !== -1) {
      matches++
      gramsBRemaining.splice(idx, 1)
    }
  }
  // Denominator must use the ORIGINAL bigram counts -- gramsBRemaining
  // shrinks as matches are spliced out above, so using its post-loop
  // length here would inflate the ratio past 1.0 (caught via a real
  // test case: "Bentch Press" vs "Bench Press" produced ratio 1.5).
  return (2 * matches) / (gramsA.length + gramsBOriginalLength)
}

export interface SimilarMatch {
  name: string
  ratio: number
  exact: boolean
}

/** candidates: distinct existing exercise names (not yet normalized). */
export function findSimilarExercise(name: string, candidates: string[], threshold = 0.85): SimilarMatch | null {
  const target = normalizeName(name)
  if (!target) return null

  let best: SimilarMatch | null = null
  for (const candidate of candidates) {
    const candidateNorm = normalizeName(candidate)
    if (candidateNorm === target) {
      return { name: candidate, ratio: 1, exact: true }
    }
    const ratio = similarityRatio(target, candidateNorm)
    if (!best || ratio > best.ratio) {
      best = { name: candidate, ratio, exact: false }
    }
  }
  return best && best.ratio >= threshold ? best : null
}
