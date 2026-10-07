import { migrate } from 'drizzle-orm/better-sqlite3/migrator'
import { db } from '../utils/db'

export default defineNitroPlugin(() => {
  migrate(db, { migrationsFolder: './server/database/migrations' })
  console.log('[db] migrations applied')
})
