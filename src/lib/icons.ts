import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import { z } from 'zod'
import { frameHexLength, scrollFrames, scrollPosterFrame } from './pixels'

/**
 * One JSON file per VMU screen in content/icons/, written by
 * `pnpm icons:import` (scripts/import.ts) and read at build time. Every screen
 * is the VMU's 48x32 1-bit LCD; see src/lib/pixels.ts for the frame encoding.
 *
 * An entry stores its frames, or a `scroll`: one wide strip the game slides
 * through the screen. A scroll is cut into frames here, on load, so everything
 * after this (thumbnails, the grid, the drawer, downloads) only sees frames.
 */
const DIR = path.join(process.cwd(), 'content/icons')

const hex = z.string().regex(/^[0-9a-f]+$/)

const scrollSchema = z.object({
	/** Width of the strip, wider than the screen; its height is the screen's. */
	width: z.number().int().min(48),
	/** The strip, encoded like a frame. */
	strip: hex,
	/** Pixels the window moves each update. */
	stepPx: z.number().int().positive(),
	/** Time between updates. */
	delayMs: z.number().int().positive()
})

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
		/** The frames; absent on a scroll entry, which stores `scroll` instead. */
		frames: z.array(hex).min(1).optional(),
		scroll: scrollSchema.optional(),
		frameDelayMs: z.number().int().positive().optional(),
		/** Delay of each frame, one per frame, for animations whose frames differ. */
		frameDelaysMs: z.array(z.number().int().positive()).optional(),
		/** Frame (from 0) the grid shows at rest, instead of the first. */
		posterFrame: z.number().int().nonnegative().optional(),
		tags: z.array(z.string()).default([]),
		/**
		 * The game's code never shows this screen (cut or leftover art). Set it
		 * only when that was checked in the code, not just because no capture
		 * caught the screen.
		 */
		unused: z.boolean().optional(),
		/** Content hash of the pixels; the importer uses it to skip duplicates. */
		hash: z.string(),
		added: z.string()
	})
	.refine(a => !a.frames !== !a.scroll, {
		message: 'set frames or scroll, not both'
	})
	.refine(
		a =>
			!a.scroll ||
			a.scroll.strip.length === frameHexLength(a.scroll.width, a.height, a.bpp),
		{ message: 'scroll strip length does not match its width x height x bpp' }
	)
	.refine(a => !(a.scroll && (a.frameDelayMs || a.frameDelaysMs)), {
		message: 'a scroll times itself with scroll.delayMs'
	})
	.transform(({ frames, ...a }) => ({
		...a,
		...(a.scroll
			? {
					frames: scrollFrames(a.scroll, a.width, a.height, a.bpp),
					frameDelayMs: a.scroll.delayMs,
					posterFrame: a.posterFrame ?? scrollPosterFrame(a.scroll, a.width)
				}
			: { frames: frames as string[] })
	}))
	.refine(
		a =>
			a.frames.every(
				f => f.length === frameHexLength(a.width, a.height, a.bpp)
			),
		{ message: 'frame length does not match width x height x bpp' }
	)
	.refine(a => (a.posterFrame ?? 0) < a.frames.length, {
		message: 'posterFrame is past the last frame'
	})
	.refine(a => !a.frameDelaysMs || a.frameDelaysMs.length === a.frames.length, {
		message: 'frameDelaysMs needs one delay per frame'
	})
	.refine(a => !(a.frameDelaysMs && a.frameDelayMs), {
		message: 'set frameDelayMs or frameDelaysMs, not both'
	})

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
	/** Only when the screen belongs to one region's release. */
	region?: IconData['region']
	/** Only when the game's code never shows the screen. */
	unused?: true
	/** Only on animations: how many frames their thumbnail strip holds. */
	frames?: number
	/** Only on animations: delay between frames, when not the default. */
	frameDelayMs?: number
	/** Only on animations whose frames last different times: each one's delay. */
	frameDelaysMs?: number[]
	/** Only on animations: the frame shown at rest, when not the first. */
	posterFrame?: number
	/** Only on scrolls: the thumbnail is the strip, cut into frames in the browser. */
	scroll?: { width: number; stepPx: number }
}

let cache: Icon[] | undefined

/** Unknown games sort after every named one. */
const gameKey = (game: string) => (game === 'Unknown' ? '￿' : game)

/**
 * Every icon, grouped by game, then by title ("Stage 2" before "Stage 10"),
 * then by id, so "amitie", "amitie-2"… keep their import order.
 */
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
				a.data.title.localeCompare(b.data.title, undefined, {
					numeric: true
				}) ||
				a.id.localeCompare(b.id, undefined, { numeric: true })
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
	tags: data.tags,
	...(data.region && { region: data.region }),
	...(data.unused && { unused: true as const }),
	...(data.frames.length > 1 && {
		frames: data.frames.length,
		frameDelayMs: data.frameDelayMs,
		frameDelaysMs: data.frameDelaysMs,
		posterFrame: data.posterFrame
	}),
	...(data.scroll && {
		scroll: { width: data.scroll.width, stepPx: data.scroll.stepPx }
	})
})
