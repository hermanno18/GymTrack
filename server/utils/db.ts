import Database from 'better-sqlite3'
import { drizzle } from 'drizzle-orm/better-sqlite3'
import { mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import * as schema from '../database/schema'

// Single-file SQLite DB, same storage model as the old Flask app's
// instance/gymtrack.db -- lives outside any publicly-served directory.
const dbPath = process.env.DATABASE_PATH || join(process.cwd(), 'data', 'gymtrack.db')
mkdirSync(dirname(dbPath), { recursive: true })

const sqlite = new Database(dbPath)
sqlite.pragma('journal_mode = WAL')
sqlite.pragma('foreign_keys = ON')

export const db = drizzle(sqlite, { schema })
