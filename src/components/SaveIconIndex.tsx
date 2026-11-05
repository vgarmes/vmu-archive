'use client'

import Fuse from 'fuse.js'
import Link from 'next/link'
import { useEffect, useMemo, useRef, useState } from 'react'
import SaveIconImage from '@/components/SaveIconImage'
import SearchBox, { NoMatches } from '@/components/SearchBox'
import type { SaveIconEntry } from '@/lib/save-icons'

/**
 * The /save-icons page: every game's save icons in one grid, and a search over
 * their titles, games (name, romanized Japanese title and other names), the
 * saves' own names
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
					{ name: 'aliases', weight: 1.5 },
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
		() => cards(q ? fuse.search(q).map(r => r.item) : icons),
		[fuse, icons, q]
	)
	const total = useMemo(() => cards(icons).length, [icons])
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
						? `${results.length} of ${total} icons`
						: `${total} icons · ${games} ${games === 1 ? 'game' : 'games'}`}
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
					{results.map(({ icon, vmu }) => (
						<SaveIconCard
							key={vmu ? `${icon.id}-vmu` : icon.id}
							icon={icon}
							vmu={vmu}
						/>
					))}
				</ul>
			)}
		</div>
	)
}

/**
 * One card per image: a memory card icon carries two, its colour icon and the
 * 1-bit one the VMU shows, and gets a card for each, side by side.
 */
const cards = (icons: SaveIconEntry[]) =>
	icons.flatMap(icon => [
		{ icon, vmu: false },
		...(icon.hasVmuIcon ? [{ icon, vmu: true }] : [])
	])

function SaveIconCard({ icon, vmu }: { icon: SaveIconEntry; vmu: boolean }) {
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
				{vmu ? (
					// The 1-bit icon the VMU shows, like the rest of the VMU art.
					<img
						src={`/save-icons/${icon.id}-vmu.png`}
						alt={`${icon.game}: ${icon.title}, on the VMU`}
						width={32}
						height={32}
						loading="lazy"
						className="pixelated aspect-square h-auto w-24 dark:invert"
					/>
				) : (
					<SaveIconImage icon={icon} className="w-24" />
				)}
			</div>
			<div className="border-border flex flex-col gap-0.5 border-t px-3 py-2 text-xs">
				<span className="truncate" title={icon.title}>
					{icon.title}
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
						{vmu ? 'VMU screen' : 'Dreamcast menu'}
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
