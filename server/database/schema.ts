import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core'
import { sql } from 'drizzle-orm'

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  weightUnit: text('weight_unit').notNull().default('kg'), // 'kg' | 'lb'
  distanceUnit: text('distance_unit').notNull().default('km'), // 'km' | 'mi'
  createdAt: text('created_at').notNull().default(sql`(current_timestamp)`),
})

export const programs = sqliteTable('programs', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  userId: integer('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  name: text('name').notNull(),
  createdAt: text('created_at').notNull().default(sql`(current_timestamp)`),
})

export const programDays = sqliteTable('program_days', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  programId: integer('program_id').notNull().references(() => programs.id, { onDelete: 'cascade' }),
  name: text('name').notNull(),
  position: integer('position').notNull().default(0),
})

export const exercises = sqliteTable('exercises', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  programDayId: integer('program_day_id').notNull().references(() => programDays.id, { onDelete: 'cascade' }),
  name: text('name').notNull(),
  position: integer('position').notNull().default(0),
  targetSets: integer('target_sets'),
  targetReps: integer('target_reps'),
  targetWeightKg: real('target_weight_kg'),
  targetDistanceKm: real('target_distance_km'),
})

export const workoutSessions = sqliteTable('workout_sessions', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  userId: integer('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  programDayId: integer('program_day_id').references(() => programDays.id, { onDelete: 'set null' }),
  performedAt: text('performed_at').notNull().default(sql`(current_timestamp)`),
  // Wall-clock "HH:MM", set only by Guided Session mode -- manual/ad-hoc
  // logging never populates these, which is exactly what lets the Story
  // timeline degrade gracefully (see workoutSets timing fields below).
  startTime: text('start_time'),
  endTime: text('end_time'),
})

export const workoutSets = sqliteTable('workout_sets', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  sessionId: integer('session_id').notNull().references(() => workoutSessions.id, { onDelete: 'cascade' }),
  // Denormalized exercise name (not a FK) so history carries over across
  // programs via name matching, per the fuzzy-matching concept in README.
  exerciseName: text('exercise_name').notNull(),
  setNumber: integer('set_number').notNull(),
  reps: integer('reps'),
  weightKg: real('weight_kg'),
  distanceKm: real('distance_km'),
  // Guided-Session-only timing, tracked per EXERCISE (not per set -- the
  // live timer accumulates work/rest across all of an exercise's sets as
  // one block). Stored only on the setNumber=1 row for that exercise/
  // session pair so summing across all rows in a session never double-
  // counts. Null for manual/ad-hoc logging.
  startedAt: text('started_at'), // "HH:MM:SS"
  workSeconds: integer('work_seconds'),
  restSeconds: integer('rest_seconds'),
})
