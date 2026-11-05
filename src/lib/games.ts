import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import { Marked } from 'marked'
import { getIcons, toIndexEntry, type Icon, type IndexEntry } from './icons'
import { getRegistry } from './registry'
import { slug } from './slug'

/**
 * The games with screens, each with a page: the screens grouped by their
 * `gameId`, plus what content/ says about each one:
 * - the registry, content/games.json (./registry), keyed by that id: the
 *   title to show (`name`), its Japanese title beneath it (`ja`), its
 *   publisher and year, its other names for the search (`aliases`), and which
 *   screen its card shows (`cover`, an icon id; by default its title screen,
 *   else its logo, else its first). A game there without screens (one with
 *   only save icons, say) has no page.
 * - content/games/<game id>.md, its notes on how the screens were extracted,
 *   shown on its page.
 */
const NOTES = path.join(process.cwd(), 'content/games')

/** What the game list and a game's header need — it ships to every visitor. */
export interface Game {
	/** The title to show, the registry's `name`. */
	name: string
	/** Its id in the registry, which is its page's route. */
	slug: string
	/** Its Japanese release's title, romanized, when it differs from `name`. */
	ja?: string
	publisher?: string
	year?: number
	/** Its other names, which the search finds it by. */
	aliases?: string[]
	/** How many icons the game has. */
	count: number
	/** The icon its card shows. */
	cover: IndexEntry
}

let cache: { game: Game; icons: Icon[]; notes?: string }[] | undefined

function load() {
	if (cache) return cache
	const registry = getRegistry()

	const byGame = new Map<string, Icon[]>()
	for (const icon of getIcons()) {
		const list = byGame.get(icon.data.gameId)
		if (list) list.push(icon)
		else byGame.set(icon.data.gameId, [icon])
	}

	const slugs = new Set<string>()
	cache = [...byGame].map(([id, icons]) => {
		const m = registry[id]
		if (!m) throw new Error(`content/games.json: no game "${id}"`)
		slugs.add(id)
		return {
			game: {
				name: m.name,
				slug: id,
				...(m.ja && { ja: m.ja }),
				publisher: m.publisher,
				year: m.year,
				...(m.aliases && { aliases: m.aliases }),
				count: icons.length,
				cover: toIndexEntry(pickCover(id, icons, m.cover))
			},
			icons,
			notes: readNotes(id)
		}
	})

	// By the title shown, Unknown last.
	const key = (g: Game) => (g.slug === 'unknown' ? '\uffff' : g.name)
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
	// they're game pages. Their images live in public/notes/<game id>/,
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
