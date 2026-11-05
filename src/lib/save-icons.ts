import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import { getGames } from './games'
import type { PixelArt } from './pixels'
import { slug } from './slug'

/**
 * Save icons (content/save-icons/<game slug>/*.json, see scripts/save-icons.ts),
 * read at build time for the /save-icons page and the game pages. Their images
 * are /save-icons/<id>.png (frame 1) and, when animated, /save-icons/<id>.gif.
 */

const DIR = path.join(process.cwd(), 'content/save-icons')

interface File {
	kind: 'save' | 'memory-card'
	title: string
	game: string
	publisher?: string
	year?: number
	region?: string
	width: number
	height: number
	bpp: 4
	palette: string[]
	frames: string[]
	animationSpeed: number
	vmuIcon?: string
	madeByGame?: boolean | null
	vmuName: string
	description: string
	source: { kind: 'save' | 'disc'; files: string[]; url?: string }
}

export interface SaveIcon {
	/** "<game slug>-<file id>", unique across games; names its images. */
	id: string
	/** A save's icon, or a memory card's own (ICONDATA_VMS). */
	kind: 'save' | 'memory-card'
	/**
	 * Memory card icons: whether the game made it (true once its disc shows
	 * it), or null until checked.
	 */
	madeByGame?: boolean | null
	/** Memory card icons: their 1-bit VMU icon, /save-icons/<id>-vmu.png. */
	hasVmuIcon: boolean
	title: string
	game: string
	gameSlug: string
	/** The game's romanized Japanese title, when the archive has it. */
	ja?: string
	/** Whether the game has a page (it has VMU screens). */
	hasPage: boolean
	publisher?: string
	year?: number
	region?: string
	vmuName: string
	description: string
	frames: number
	/** How many saves carry it, and where they came from. */
	saves: number
	sourceUrl?: string
	art: PixelArt
	/** The 1-bit VMU icon of a memory card icon. */
	vmuArt?: PixelArt
}

let cache: SaveIcon[] | undefined

export function getSaveIcons(): SaveIcon[] {
	if (cache) return cache
	const games = new Map(getGames().map(g => [g.slug, g]))
	cache = []
	if (!fs.existsSync(DIR)) return cache
	for (const gameSlug of fs.readdirSync(DIR).sort()) {
		const dir = path.join(DIR, gameSlug)
		if (!fs.statSync(dir).isDirectory()) continue
		for (const file of fs
			.readdirSync(dir)
			.filter(f => f.endsWith('.json'))
			.sort()) {
			const s = JSON.parse(
				fs.readFileSync(path.join(dir, file), 'utf8')
			) as File
			const game = games.get(slug(s.game))
			cache.push({
				id: `${gameSlug}-${file.replace(/\.json$/, '')}`,
				kind: s.kind,
				madeByGame: s.madeByGame,
				hasVmuIcon: !!s.vmuIcon,
				title: s.title,
				game: game?.en ?? s.game,
				gameSlug,
				ja: game?.ja,
				hasPage: !!game,
				publisher: s.publisher,
				year: s.year,
				region: s.region,
				vmuName: s.vmuName,
				description: s.description,
				frames: s.frames.length,
				saves: s.source.files.length,
				sourceUrl: s.source.url,
				art: {
					width: s.width,
					height: s.height,
					bpp: 4,
					palette: s.palette,
					frames: s.frames
				},
				vmuArt: s.vmuIcon
					? { width: 32, height: 32, bpp: 1, frames: [s.vmuIcon] }
					: undefined
			})
		}
	}
	// Games in title order, a game's icons in file order.
	cache.sort((a, b) => a.game.localeCompare(b.game))
	return cache
}

export const getSaveIcon = (id: string) => getSaveIcons().find(i => i.id === id)

/** A game's save icons, for its page. */
export const getGameSaveIcons = (gameSlug: string) =>
	getSaveIcons().filter(i => i.gameSlug === gameSlug)

/** What the browser needs: everything but the pixels. */
export type SaveIconEntry = Omit<SaveIcon, 'art' | 'vmuArt'>
export const toEntry = ({
	art: _art,
	vmuArt: _vmuArt,
	...rest
}: SaveIcon): SaveIconEntry => rest
