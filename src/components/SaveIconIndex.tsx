'use client'

import Fuse from 'fuse.js'
import Link from 'next/link'
import { useEffect, useMemo, useRef, useState } from 'react'
import SaveIconImage from '@/components/SaveIconImage'
import SearchBox, { NoMatches } from '@/components/SearchBox'
import type { SaveIconEntry } from '@/lib/save-icons'

/**
 * The /save-icons page: every game's save icons in one grid, and a search over
 * their titles, games (English and romanized Japanese), the saves' own names
 * and descriptions, and publishers, kept in the URL as ?q=.
 */
export default function SaveIconIndex({ icons }: { icons: SaveIconEntry[] }) {
	const [query, setQuery] = useState('')
	const [restored, setRestored] = useState(false)
	const searchRef = useRef<HTMLInputElement>(null)

	useEffect(() => {
		setQuery(new URLSearchParams(location.search).get('q') ?? '')
		setRestored(true)
	}, [])

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
			new Fuse(icons, {
				keys: [
					{ name: 'game', weight: 2 },
					{ name: 'ja', weight: 2 },
					{ name: 'title', weight: 1.5 },
					{ name: 'vmuName', weight: 0.5 },
					{ name: 'description', weight: 0.5 },
					{ name: 'publisher', weight: 0.5 },
					{ name: 'year', weight: 0.5, getFn: i => String(i.year ?? '') }
				],
				threshold: 0.35,
				ignoreLocation: true,
				ignoreDiacritics: true
			}),
		[icons]
	)

	const q = query.trim()
	const results = useMemo(
		() => (q ? fuse.search(q).map(r => r.item) : icons),
		[fuse, icons, q]
	)
	const games = new Set(icons.map(i => i.gameSlug)).size

	return (
		<div className="flex flex-col gap-6">
			<div className="flex flex-col gap-3">
				<SearchBox
					value={query}
					onChange={setQuery}
					placeholder="Search by game or kind of save…"
					label="Search save icons"
					inputRef={searchRef}
				/>
				<span
					className="text-muted-foreground text-right text-sm"
					aria-live="polite"
				>
					{q
						? `${results.length} of ${icons.length} icons`
						: `${icons.length} icons · ${games} ${games === 1 ? 'game' : 'games'}`}
				</span>
			</div>

			{results.length === 0 ? (
				<NoMatches
					message={`No save icon matches “${query}”.`}
					onClear={() => {
						setQuery('')
						searchRef.current?.focus()
					}}
				/>
			) : (
				<ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
					{results.map(icon => (
						<SaveIconCard key={icon.id} icon={icon} />
					))}
				</ul>
			)}
		</div>
	)
}

function SaveIconCard({ icon }: { icon: SaveIconEntry }) {
	const game = icon.hasPage ? (
		<Link
			href={`/games/${icon.gameSlug}`}
			className="hover:text-foreground truncate underline-offset-2 hover:underline"
		>
			{icon.game}
		</Link>
	) : (
		<span className="truncate">{icon.game}</span>
	)
	return (
		<li className="border-border bg-card hover:border-foreground flex flex-col border">
			<div className="flex items-center justify-center gap-3 p-4">
				{icon.hasVmuIcon ? (
					<>
						<SaveIconImage icon={icon} className="w-16" />
						{/* The 1-bit icon the VMU shows, like the rest of the VMU art. */}
						<img
							src={`/save-icons/${icon.id}-vmu.png`}
							alt={`${icon.game}: ${icon.title}, on the VMU`}
							width={32}
							height={32}
							loading="lazy"
							className="pixelated aspect-square h-auto w-16 dark:invert"
						/>
					</>
				) : (
					<SaveIconImage icon={icon} className="w-24" />
				)}
			</div>
			<div className="border-border flex flex-col gap-0.5 border-t px-3 py-2 text-xs">
				<span className="flex items-baseline justify-between gap-2">
					<span className="truncate" title={icon.title}>
						{icon.title}
					</span>
					<span
						className="text-muted-foreground shrink-0 tabular-nums"
						title={`Carried by ${icon.saves} ${icon.saves === 1 ? 'save' : 'saves'}`}
					>
						{icon.saves}
					</span>
				</span>
				<span className="text-muted-foreground flex min-w-0">{game}</span>
				<span
					className="text-muted-foreground/70 truncate"
					title={icon.description}
					lang="ja"
				>
					{icon.vmuName}
				</span>
				{icon.kind === 'memory-card' && (
					<span className="text-muted-foreground/70">
						Memory card icon
						{icon.madeByGame === null && (
							<span title="Not yet found on the game's disc: it may be the game's, or made with a tool">
								{' '}
								· unverified
							</span>
						)}
					</span>
				)}
			</div>
		</li>
	)
}
