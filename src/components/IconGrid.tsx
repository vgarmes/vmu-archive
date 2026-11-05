'use client'

import Fuse from 'fuse.js'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import RegionFlag from '@/components/RegionFlag'
import SearchBox, { NoMatches } from '@/components/SearchBox'
import SpriteDrawer from '@/components/SpriteDrawer'
import { Thumb, useHoverGif } from '@/components/Thumb'
import type { IndexEntry } from '@/lib/icons'

/**
 * A game's screens: a search box and the grid.
 *
 * The page prerenders every card's metadata, so the grid shows up without
 * JS. Cards are rendered in batches as the visitor scrolls (the svgl
 * pattern) rather than virtualised — each card is one lazy-loaded <img>.
 *
 * Clicking a card opens the sprite drawer and adds ?screen=<id> to the URL
 * (Back closes it, and a shared link opens it); the search is kept as ?q=.
 * Animated cards show a still and play their GIF on hover or keyboard focus
 * (see `useHoverGif`), unless the visitor asks for reduced motion.
 */

const BATCH = 60

export default function IconGrid({ icons }: { icons: IndexEntry[] }) {
	const [query, setQuery] = useState('')
	const searchRef = useRef<HTMLInputElement>(null)
	const [shown, setShown] = useState(BATCH)
	const [screen, setScreen] = useState<string | null>(null)
	// Whether `query` and `screen` have been read from the URL yet. Until then
	// the URL is the only copy of them, so nothing may overwrite it.
	const [restored, setRestored] = useState(false)
	// Whether the open drawer added a history entry, so closing can go Back.
	const pushed = useRef(false)
	const sentinel = useRef<HTMLDivElement>(null)

	// Restore state from the URL.
	useEffect(() => {
		const params = new URLSearchParams(location.search)
		setQuery(params.get('q') ?? '')
		setScreen(params.get('screen'))
		setRestored(true)
		const onPop = () => {
			pushed.current = false
			setScreen(new URLSearchParams(location.search).get('screen'))
		}
		addEventListener('popstate', onPop)
		return () => removeEventListener('popstate', onPop)
	}, [])

	const urlFor = useCallback(
		(screen: string | null) => {
			// Keep what else is in the URL (the game page's ?tab=).
			const params = new URLSearchParams(location.search)
			params.delete('q')
			params.delete('screen')
			if (query) params.set('q', query)
			if (screen) params.set('screen', screen)
			const qs = params.toString()
			return qs ? `?${qs}` : location.pathname
		},
		[query]
	)

	// Keep the URL shareable as the search changes. Not before the URL has been
	// read: on the first render `screen` is still null, and writing then would
	// drop the ?screen= of a shared link.
	useEffect(() => {
		if (!restored) return
		history.replaceState(null, '', urlFor(screen))
		setShown(BATCH)
		// eslint-disable-next-line react-hooks/exhaustive-deps -- only on search changes
	}, [query, restored])

	const openScreen = (id: string) => {
		history.pushState(null, '', urlFor(id))
		pushed.current = true
		setScreen(id)
	}
	const closeScreen = () => {
		if (pushed.current) {
			// popstate clears `screen`.
			history.back()
		} else {
			history.replaceState(null, '', urlFor(null))
			setScreen(null)
		}
	}
	const selected = screen ? (icons.find(i => i.id === screen) ?? null) : null

	const fuse = useMemo(
		() =>
			new Fuse(icons, {
				keys: [
					{ name: 'title', weight: 2 },
					'tags',
					{ name: 'unused', getFn: i => (i.unused ? 'unused' : '') }
				],
				threshold: 0.35,
				ignoreLocation: true,
				ignoreDiacritics: true
			}),
		[icons]
	)

	const results = useMemo(() => {
		const q = query.trim()
		return q ? fuse.search(q).map(r => r.item) : icons
	}, [fuse, icons, query])

	// Render the next batch as the end of the grid nears the viewport.
	useEffect(() => {
		const el = sentinel.current
		if (!el) return
		const observer = new IntersectionObserver(
			entries => {
				if (entries[0].isIntersecting)
					setShown(n => Math.min(n + BATCH, results.length))
			},
			{ rootMargin: '600px' }
		)
		observer.observe(el)
		return () => observer.disconnect()
	}, [results.length])

	const clear = () => {
		setQuery('')
		searchRef.current?.focus()
	}

	return (
		<div className="flex flex-col gap-6">
			<div className="flex flex-col gap-3">
				<SearchBox
					value={query}
					onChange={setQuery}
					placeholder="Search this game's screens by title or tag…"
					label="Search screens"
					inputRef={searchRef}
				/>
				<span
					className="text-muted-foreground text-right text-sm"
					aria-live="polite"
				>
					{query ? `${results.length} of ${icons.length}` : icons.length}{' '}
					{icons.length === 1 ? 'screen' : 'screens'}
				</span>
			</div>

			{results.length === 0 ? (
				<NoMatches message={`Nothing matches “${query}”.`} onClear={clear} />
			) : (
				<ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
					{results.slice(0, shown).map(icon => (
						<Card key={icon.id} icon={icon} onOpen={openScreen} />
					))}
				</ul>
			)}
			<div ref={sentinel} className="h-px" />
			<SpriteDrawer entry={selected} onClose={closeScreen} />
		</div>
	)
}

function Card({
	icon,
	onOpen
}: {
	icon: IndexEntry
	onOpen: (id: string) => void
}) {
	const gif = useHoverGif(icon)
	return (
		<li className="[contain-intrinsic-size:auto_160px] [content-visibility:auto]">
			{/* A real link, so new-tab and copy-link still work; a plain click opens the drawer. */}
			<a
				href={`?screen=${icon.id}`}
				onClick={e => {
					if (
						e.button !== 0 ||
						e.metaKey ||
						e.ctrlKey ||
						e.shiftKey ||
						e.altKey
					)
						return
					e.preventDefault()
					onOpen(icon.id)
				}}
				{...gif.handlers}
				className="group border-border bg-card hover:border-foreground focus-visible:ring-ring flex h-full flex-col border outline-none focus-visible:ring-2"
			>
				<Thumb icon={icon} gifSrc={gif.src} />
				<span className="border-border flex items-baseline justify-between gap-2 border-t px-3 py-2 text-xs">
					<span className="truncate">{icon.title}</span>
					{(icon.unused || icon.region) && (
						<span className="flex shrink-0 items-center gap-1.5 self-center">
							{icon.unused && (
								<span className="text-muted-foreground">Unused</span>
							)}
							<RegionFlag region={icon.region} />
						</span>
					)}
				</span>
			</a>
		</li>
	)
}
