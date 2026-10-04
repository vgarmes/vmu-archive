import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import { z } from 'zod'
import { frameHexLength } from './pixels'

/**
 * One JSON file per VMU screen in content/icons/, written by
 * `pnpm icons:import` (scripts/import.ts) and read at build time. Every screen
 * is the VMU's 48x32 1-bit LCD; see src/lib/pixels.ts for the frame encoding.
 */
const DIR = path.join(process.cwd(), 'content/icons')

const schema = z
	.object({
		title: z.string(),
		game: z.string(),
		publisher: z.string().optional(),
		year: z.number().int().optional(),
		region: z.enum(['JP', 'US', 'EU', 'WW']).optional(),
		width: z.literal(48),
		height: z.literal(32),
		bpp: z.literal(1),
		frames: z.array(z.string().regex(/^[0-9a-f]+$/)).min(1),
		frameDelayMs: z.number().int().positive().optional(),
		tags: z.array(z.string()).default([]),
		/** Content hash of the pixels; the importer uses it to skip duplicates. */
		hash: z.string(),
		added: z.string()
	})
	.refine(
		a =>
			a.frames.every(
				f => f.length === frameHexLength(a.width, a.height, a.bpp)
			),
		{ message: 'frame length does not match width x height x bpp' }
	)

export type IconData = z.infer<typeof schema>
export interface Icon {
	id: string
	data: IconData
}

/** The fields the grid and search need — keep this small, it ships to every visitor. */
export interface IndexEntry {
	id: string
	title: string
	game: string
	publisher?: string
	year?: number
	tags: string[]
}

let cache: Icon[] | undefined

/** Unknown games sort after every named one. */
const gameKey = (game: string) => (game === 'Unknown' ? '￿' : game)

/** Every icon, grouped by game, then by title ("Amitie 2" before "Amitie 10"). */
export function getIcons(): Icon[] {
	cache ??= fs
		.readdirSync(DIR)
		.filter(f => f.endsWith('.json'))
		.map(file => {
			const id = file.replace(/\.json$/, '')
			const parsed = schema.safeParse(
				JSON.parse(fs.readFileSync(path.join(DIR, file), 'utf8'))
			)
			if (!parsed.success)
				throw new Error(`content/icons/${file}: ${parsed.error.message}`)
			return { id, data: parsed.data }
		})
		.sort(
			(a, b) =>
				gameKey(a.data.game).localeCompare(gameKey(b.data.game)) ||
				a.data.title.localeCompare(b.data.title, undefined, { numeric: true })
		)
	return cache
}

export const getIcon = (id: string) => getIcons().find(icon => icon.id === id)

export const toIndexEntry = ({ id, data }: Icon): IndexEntry => ({
	id,
	title: data.title,
	game: data.game,
	publisher: data.publisher,
	year: data.year,
	tags: data.tags
})
