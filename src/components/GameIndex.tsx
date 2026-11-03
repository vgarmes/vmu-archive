'use client'

import Fuse from 'fuse.js'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useMemo, useRef, useState } from 'react'
import SearchBox, { NoMatches } from '@/components/SearchBox'
import { Thumb, useHoverGif } from '@/components/Thumb'
import type { Game } from '@/lib/games'

/**
 * The home page: every game as a card showing its cover screen, and a search
 * over their English and romanized Japanese titles (and publishers), kept in
 * the URL as ?q=.
 *
 * Links from before game pages existed (?game=<slug>, ?screen=<id>) are sent
 * on to the game's page.
 */

export default function GameIndex({ games }: { games: Game[] }) {
	const router = useRouter()
	const [query, setQuery] = useState('')
	const [restored, setRestored] = useState(false)
	const searchRef = useRef<HTMLInputElement>(null)

	useEffect(() => {
		const params = new URLSearchParams(location.search)
		const screen = params.get('screen')
		// Icon ids start with their game's slug; take the longest that fits.
		const game =
			games.find(g => g.slug === params.get('game')) ??
			(screen
				? games
						.filter(g => screen.startsWith(`${g.slug}-`))
						.sort((a, b) => b.slug.length - a.slug.length)[0]
				: undefined)
		if (game) {
			router.replace(
				`/games/${game.slug}${screen ? `?screen=${encodeURIComponent(screen)}` : ''}`
			)
			return
		}
		setQuery(params.get('q') ?? '')
		setRestored(true)
	}, [games, router])

	useEffect(() => {
		if (!restored) return
		history.replaceState(
			null,
			'',
			query ? `?${new URLSearchParams({ q: query })}` : location.pathname
		)
	}, [query, restored])

	const fuse = useMemo(
		() =>
			new Fuse(games, {
				keys: [
					{ name: 'en', weight: 2 },
					{ name: 'ja', weight: 2 },
					{ name: 'publisher', weight: 0.5 },
					{ name: 'year', weight: 0.5, getFn: g => String(g.year ?? '') }
				],
				threshold: 0.35,
				ignoreLocation: true,
				ignoreDiacritics: true
			}),
		[games]
	)

	const q = query.trim()
	const results = useMemo(
		() => (q ? fuse.search(q).map(r => r.item) : games),
		[fuse, games, q]
	)
	const screens = games.reduce((n, g) => n + g.count, 0)

	return (
		<div className="flex flex-col gap-6">
			<div className="flex flex-col gap-3">
				<SearchBox
					value={query}
					onChange={setQuery}
					placeholder="Search by English or Japanese title…"
					label="Search games"
					inputRef={searchRef}
				/>
				<span
					className="text-muted-foreground text-right text-sm"
					aria-live="polite"
				>
					{q
						? `${results.length} of ${games.length} games`
						: `${games.length} games · ${screens} screens`}
				</span>
			</div>

			{results.length === 0 ? (
				<NoMatches
					message={`No game matches “${query}”.`}
					onClear={() => {
						setQuery('')
						searchRef.current?.focus()
					}}
				/>
			) : (
				<ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
					{results.map(game => (
						<GameCard key={game.slug} game={game} />
					))}
				</ul>
			)}
		</div>
	)
}

function GameCard({ game }: { game: Game }) {
	const gif = useHoverGif(game.cover)
	return (
		<li>
			<Link
				href={`/games/${game.slug}`}
				{...gif.handlers}
				className="group border-border bg-card hover:border-foreground focus-visible:ring-ring flex h-full flex-col border outline-none focus-visible:ring-2"
			>
				<Thumb icon={game.cover} gifSrc={gif.src} />
				<span className="border-border flex flex-col gap-0.5 border-t px-3 py-2 text-xs">
					<span className="flex items-baseline justify-between gap-2">
						<span className="truncate" title={game.en}>
							{game.en}
						</span>
						<span
							className="text-muted-foreground shrink-0 tabular-nums"
							aria-label={`${game.count} ${game.count === 1 ? 'screen' : 'screens'}`}
						>
							{game.count}
						</span>
					</span>
					<span className="text-muted-foreground truncate" title={game.ja}>
						{game.ja ?? ' '}
					</span>
				</span>
			</Link>
		</li>
	)
}
