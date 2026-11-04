import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import { Marked } from 'marked'
import { z } from 'zod'
import { getIcons, toIndexEntry, type Icon, type IndexEntry } from './icons'
import { slug } from './slug'

/**
 * The games, built from the icons' `game` field, plus what content/ says
 * about each one:
 * - content/games.json, keyed by the game's name (the icons' `game`, which
 *   also gives its slug): its English and romanized Japanese titles where
 *   they differ, and which screen its card shows (`cover`, an icon id; by
 *   default its title screen, else its logo, else its first).
 * - content/games/<game slug>.md, its notes on how the screens were
 *   extracted, shown on its page.
 */
const META = path.join(process.cwd(), 'content/games.json')
const NOTES = path.join(process.cwd(), 'content/games')

const metaSchema = z.record(
	z.string(),
	z.strictObject({
		/**
		 * The English release's title, when the game's name is the Japanese
		 * one ("Berserk: Millennium Falcon-hen…" → "Sword of the Berserk…").
		 */
		en: z.string().optional(),
		/**
		 * The Japanese release's title, romanized, when the game's name is the
		 * English one ("Project Justice" → "Moero! Justice Gakuen").
		 */
		ja: z.string().optional(),
		/** Id of the icon its card shows. */
		cover: z.string().optional()
	})
)

/** What the game list and a game's header need — it ships to every visitor. */
export interface Game {
	/** The icons' `game`; only the slug and lookups use it. */
	name: string
	slug: string
	/** The title to show: the English one. */
	en: string
	/** The romanized Japanese title, when it differs from `en`. */
	ja?: string
	publisher?: string
	year?: number
	/** How many icons the game has. */
	count: number
	/** The icon its card shows. */
	cover: IndexEntry
}

let cache: { game: Game; icons: Icon[]; notes?: string }[] | undefined

function load() {
	if (cache) return cache
	const meta = metaSchema.parse(JSON.parse(fs.readFileSync(META, 'utf8')))

	const byGame = new Map<string, Icon[]>()
	for (const icon of getIcons()) {
		const list = byGame.get(icon.data.game)
		if (list) list.push(icon)
		else byGame.set(icon.data.game, [icon])
	}
	for (const name of Object.keys(meta))
		if (!byGame.has(name))
			throw new Error(`content/games.json: no icons for "${name}"`)

	const slugs = new Set<string>()
	cache = [...byGame].map(([name, icons]) => {
		const m = meta[name] ?? {}
		if (m.en && m.ja)
			throw new Error(
				`content/games.json: "${name}" is one of its titles; set en or ja, not both`
			)
		const s = slug(name)
		slugs.add(s)
		const ja = m.ja ?? (m.en ? name : undefined)
		const first = <K extends 'publisher' | 'year'>(key: K) =>
			icons.find(i => i.data[key] !== undefined)?.data[key]
		return {
			game: {
				name,
				slug: s,
				en: m.en ?? name,
				...(ja && { ja }),
				publisher: first('publisher'),
				year: first('year'),
				count: icons.length,
				cover: toIndexEntry(pickCover(name, icons, m.cover))
			},
			icons,
			notes: readNotes(s)
		}
	})

	// By the title shown, Unknown last.
	const key = (g: Game) => (g.name === 'Unknown' ? '\uffff' : g.en)
	cache.sort((a, b) => key(a.game).localeCompare(key(b.game)))

	for (const file of fs.readdirSync(NOTES))
		if (file.endsWith('.md') && !slugs.has(file.replace(/\.md$/, '')))
			throw new Error(`content/games/${file}: no game has this slug`)
	return cache
}

function pickCover(name: string, icons: Icon[], id?: string) {
	if (id) {
		const icon = icons.find(i => i.id === id)
		if (!icon)
			throw new Error(`content/games.json: "${name}" has no icon "${id}"`)
		return icon
	}
	const used = icons.filter(i => !i.data.unused)
	const titles = used.filter(i => /^title screen$/i.test(i.data.title))
	return (
		titles.find(i => !i.data.region) ??
		titles[0] ??
		used.find(i => /\blogo\b/i.test(i.data.title)) ??
		used[0] ??
		icons[0]
	)
}

const markdown = new Marked({
	// Notes link to each other as files ("power-stone-2.md"); on the site
	// they're game pages. Their images live in public/notes/<game slug>/,
	// written relative to the notes file so they also show on GitHub
	// ("../../public/notes/…"); on the site public/ is the root.
	walkTokens(token) {
		if (token.type === 'link')
			token.href = token.href.replace(
				/^(?:\.\/)?([a-z0-9-]+)\.md(#.*)?$/,
				'/games/$1$2'
			)
		if (token.type === 'image')
			token.href = token.href.replace(/^(?:\.\.\/)+public\//, '/')
	},
	renderer: {
		// Ids for the notes' own #links ("see [Waiting](#waiting)").
		heading({ tokens, depth, text }) {
			return `<h${depth} id="${slug(text)}">${this.parser.parseInline(tokens)}</h${depth}>\n`
		}
	}
})

function readNotes(gameSlug: string) {
	const file = path.join(NOTES, `${gameSlug}.md`)
	if (!fs.existsSync(file)) return undefined
	const source = fs.readFileSync(file, 'utf8')
	// The page has its own heading.
	const body = source.replace(/^# .+\n+/, '')
	return markdown.parse(body, { async: false })
}

/** Every game with at least one icon, by English title (Unknown last). */
export const getGames = (): Game[] => load().map(g => g.game)

/** A game, its icons in the grid's order, and its notes as HTML. */
export const getGame = (gameSlug: string) =>
	load().find(g => g.game.slug === gameSlug)
