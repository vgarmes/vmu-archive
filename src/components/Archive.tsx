'use client'

import Fuse from 'fuse.js'
import Link from 'next/link'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { IndexEntry } from '@/lib/icons'

/**
 * Search box, filters and the icon grid.
 *
 * The page prerenders the first batch (`initial`) so the grid shows up
 * without JS; the full metadata index is fetched once on load. Cards are
 * rendered in batches as the visitor scrolls (the svgl pattern) rather than
 * virtualised — each card is one lazy-loaded <img>, so even thousands stay
 * light, and search keeps most result sets small.
 */

const BATCH = 60

interface Props {
	initial: IndexEntry[]
	total: number
}

export default function Archive({ initial, total }: Props) {
	const [index, setIndex] = useState<IndexEntry[]>(initial)
	const [query, setQuery] = useState('')
	const [animatedOnly, setAnimatedOnly] = useState(false)
	const [shown, setShown] = useState(BATCH)
	const sentinel = useRef<HTMLDivElement>(null)

	// Restore state from the URL, then load the full index.
	useEffect(() => {
		const params = new URLSearchParams(location.search)
		setQuery(params.get('q') ?? '')
		setAnimatedOnly(params.has('animated'))

		fetch('/search-index.json')
			.then(r => r.json())
			.then(setIndex)
			.catch(() => {})
	}, [])

	// Keep the URL shareable.
	useEffect(() => {
		const params = new URLSearchParams()
		if (query) params.set('q', query)
		if (animatedOnly) params.set('animated', '')
		const qs = params.toString().replace(/=(?=&|$)/g, '')
		history.replaceState(null, '', qs ? `?${qs}` : location.pathname)
		setShown(BATCH)
	}, [query, animatedOnly])

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
		const base = query.trim()
			? fuse.search(query.trim()).map(r => r.item)
			: index
		return animatedOnly ? base.filter(i => i.anim) : base
	}, [fuse, index, query, animatedOnly])

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
	const filtered = query || animatedOnly

	return (
		<div className="flex flex-col gap-6">
			<div className="flex flex-col gap-3">
				<input
					type="search"
					value={query}
					onChange={e => setQuery(e.currentTarget.value)}
					placeholder="Search by title, game, publisher or tag…"
					aria-label="Search icons"
					className="border-input bg-background focus-visible:ring-ring w-full border px-4 py-3 text-base outline-none focus-visible:ring-2"
				/>
				<div className="flex flex-wrap items-center gap-2 text-sm">
					<button
						type="button"
						aria-pressed={animatedOnly}
						onClick={() => setAnimatedOnly(a => !a)}
						className="border-border text-muted-foreground hover:text-foreground aria-pressed:bg-primary aria-pressed:text-primary-foreground aria-pressed:border-primary border px-3 py-1 uppercase"
					>
						Animated
					</button>
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
						<Card key={icon.id} icon={icon} />
					))}
				</ul>
			)}
			<div ref={sentinel} className="h-px" />
		</div>
	)
}

function Card({ icon }: { icon: IndexEntry }) {
	return (
		<li className="[contain-intrinsic-size:auto_200px] [content-visibility:auto]">
			<Link
				href={`/icon/${icon.id}`}
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
						// The art is near-black; flip it for dark mode.
						className="pixelated absolute inset-0 m-auto size-4/5 object-contain dark:invert"
					/>
				</div>
				<div className="border-border flex flex-col gap-0.5 border-t px-3 py-2 text-xs">
					<div className="flex items-baseline justify-between gap-2">
						<span className="truncate">{icon.title}</span>
						{icon.anim && (
							<span className="text-muted-foreground shrink-0 uppercase">
								Anim
							</span>
						)}
					</div>
					<span className="text-muted-foreground truncate">
						{icon.game === icon.title ? '\u00a0' : icon.game}
					</span>
				</div>
			</Link>
		</li>
	)
}
