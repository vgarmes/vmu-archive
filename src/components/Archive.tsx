'use client'

import { Input } from '@base-ui/react/input'
import { cn } from 'cn'
import Fuse from 'fuse.js'
import {
	type CSSProperties,
	useCallback,
	useEffect,
	useMemo,
	useRef,
	useState
} from 'react'
import SpriteDrawer from '@/components/SpriteDrawer'
import type { IndexEntry } from '@/lib/icons'
import { DEFAULT_FRAME_DELAY_MS, stripPosition } from '@/lib/pixels'

/**
 * Search box, filters and the icon grid.
 *
 * The page prerenders the first batch (`initial`) so the grid shows up
 * without JS; the full metadata index is fetched once on load. Cards are
 * rendered in batches as the visitor scrolls (the svgl pattern) rather than
 * virtualised — each card is one lazy-loaded <img>, so even thousands stay
 * light, and search keeps most result sets small.
 *
 * Clicking a card opens the sprite drawer and adds ?screen=<id> to the URL
 * (Back closes it, and a shared link opens it). Animated cards play on hover
 * or keyboard focus, in CSS alone (see `animate-frames`).
 */

const BATCH = 60

interface Props {
	initial: IndexEntry[]
	total: number
}

export default function Archive({ initial, total }: Props) {
	const [index, setIndex] = useState<IndexEntry[]>(initial)
	const [query, setQuery] = useState('')
	const [shown, setShown] = useState(BATCH)
	const [screen, setScreen] = useState<string | null>(null)
	// Whether `query` and `screen` have been read from the URL yet. Until then
	// the URL is the only copy of them, so nothing may overwrite it.
	const [restored, setRestored] = useState(false)
	// Whether the open drawer added a history entry, so closing can go Back.
	const pushed = useRef(false)
	const sentinel = useRef<HTMLDivElement>(null)

	// Restore state from the URL, then load the full index.
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

		fetch('/search-index.json')
			.then(r => r.json())
			.then(setIndex)
			.catch(() => {})
		return () => removeEventListener('popstate', onPop)
	}, [])

	const urlFor = useCallback(
		(screen: string | null) => {
			const params = new URLSearchParams()
			if (query) params.set('q', query)
			if (screen) params.set('screen', screen)
			const qs = params.toString().replace(/=(?=&|$)/g, '')
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
	const selected = screen ? (index.find(i => i.id === screen) ?? null) : null

	const fuse = useMemo(
		() =>
			new Fuse(index, {
				keys: [
					{ name: 'title', weight: 2 },
					{ name: 'game', weight: 1.5 },
					'publisher',
					'tags',
					{ name: 'year', getFn: i => String(i.year ?? '') }
				],
				threshold: 0.35,
				ignoreLocation: true
			}),
		[index]
	)

	const results = useMemo(() => {
		const q = query.trim()
		return q ? fuse.search(q).map(r => r.item) : index
	}, [fuse, index, query])

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

	const visible = results.slice(0, shown)
	const filtered = !!query

	return (
		<div className="flex flex-col gap-6">
			<div className="flex flex-col gap-3">
				<div
					role="search"
					className="border-border bg-card/50 focus-within:border-foreground focus-within:ring-foreground/30 box-border flex h-9 max-h-9 min-h-9 min-w-0 flex-1 items-center gap-2 border px-3 transition-[border-color,box-shadow] focus-within:ring-1"
				>
					<svg
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						strokeWidth="2"
						strokeLinecap="round"
						strokeLinejoin="round"
						className="text-muted-foreground h-4 w-4 shrink-0"
						aria-hidden="true"
					>
						<path d="m21 21-4.34-4.34" />
						<circle cx="11" cy="11" r="8" />
					</svg>
					<Input
						type="text"
						enterKeyHint="search"
						value={query}
						onValueChange={setQuery}
						placeholder="Search by title, game, publisher or tag…"
						aria-label="Search icons"
						className="placeholder:text-muted-foreground h-full min-h-0 w-full min-w-0 flex-1 border-0 bg-transparent py-0 font-mono text-sm leading-5 ring-0 outline-none focus:outline-none"
					/>
				</div>
				<div className="flex flex-wrap items-center gap-2 text-sm">
					<span className="text-muted-foreground ml-auto" aria-live="polite">
						{filtered ? `${results.length} of ${total}` : total} icons
					</span>
				</div>
			</div>

			{results.length === 0 ? (
				<p className="text-muted-foreground py-16 text-center">
					Nothing matches “{query}”.
				</p>
			) : (
				<ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
					{visible.map(icon => (
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
	return (
		<li className="[contain-intrinsic-size:auto_200px] [content-visibility:auto]">
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
				className="group border-border bg-card hover:border-foreground focus-visible:ring-ring flex h-full flex-col border outline-none focus-visible:ring-2"
			>
				{/*
					The image is absolutely positioned so it can't stretch the 3:2 box;
					a percentage height on an in-flow image let Safari grow the box.
				*/}
				<div className="relative aspect-[3/2]">
					<img
						src={`/thumbs/${icon.id}.png`}
						alt=""
						width={48}
						height={32}
						loading="lazy"
						decoding="async"
						// The art is near-black; flip it for dark mode. An animation's
						// thumbnail is a strip of frames: show the first, play on hover.
						className={cn(
							'pixelated absolute inset-0 m-auto size-4/5 dark:invert',
							icon.frames
								? 'motion-safe:group-hover:animate-frames motion-safe:group-focus-visible:animate-frames object-cover object-top'
								: 'object-contain'
						)}
						style={
							icon.frames
								? ({
										'--frames': icon.frames,
										'--frame-delay': `${icon.frameDelayMs ?? DEFAULT_FRAME_DELAY_MS}ms`,
										// At rest, the poster frame; the hover animation overrides it.
										...(icon.posterFrame && {
											objectPosition: stripPosition(
												icon.frames,
												icon.posterFrame
											)
										})
									} as CSSProperties)
								: undefined
						}
					/>
				</div>
				<div className="border-border flex flex-col gap-0.5 border-t px-3 py-2 text-xs">
					<span className="truncate">{icon.title}</span>
					<span className="text-muted-foreground truncate">
						{icon.game === icon.title ? '\u00a0' : icon.game}
					</span>
				</div>
			</a>
		</li>
	)
}
