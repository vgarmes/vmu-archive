import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import GameTabs, { type GameTab } from '@/components/GameTabs'
import IconGrid from '@/components/IconGrid'
import SaveIconImage from '@/components/SaveIconImage'
import SpritesPanel, { FontsPanel } from '@/components/SpriteSheet'
import {
	Breadcrumb,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbList,
	BreadcrumbPage,
	BreadcrumbSeparator
} from '@/components/ui/breadcrumb'
import { getGame, getGames } from '@/lib/games'
import { toIndexEntry } from '@/lib/icons'
import { getGameSaveIcons, toEntry } from '@/lib/save-icons'
import { getSpriteSheet } from '@/lib/sprites'

export const dynamicParams = false

/** Save icons shown beside the title; the rest are a link away. */
const HEADER_SAVE_ICONS = 3

export function generateStaticParams() {
	return getGames().map(g => ({ slug: g.slug }))
}

export async function generateMetadata({
	params
}: PageProps<'/games/[slug]'>): Promise<Metadata> {
	const found = getGame((await params).slug)
	if (!found) return {}
	const { game } = found
	return {
		title: game.name,
		description: `${game.count} VMU ${game.count === 1 ? 'screen' : 'screens'} from ${game.name}${game.ja ? ` (${game.ja})` : ''}, free to download.`
	}
}

export default async function GamePage({ params }: PageProps<'/games/[slug]'>) {
	const found = getGame((await params).slug)
	if (!found) notFound()
	const { game, icons, notes } = found
	const sheet = getSpriteSheet(game.slug)
	const saveIcons = getGameSaveIcons(game.slug)
	// Its main, system and save files' icons first (the ones every player
	// has), then its other saves' (downloads, replays…), then its memory
	// card's; each group in file order.
	const rank = (i: (typeof saveIcons)[number]) =>
		i.kind !== 'save' ? 2 : /\b(main|system|save)\b/i.test(i.title) ? 0 : 1
	const headerIcons = [...saveIcons]
		.sort((a, b) => rank(a) - rank(b))
		.slice(0, HEADER_SAVE_ICONS)
	const allSaveIcons = `/save-icons?${new URLSearchParams({ q: game.name })}`
	const meta = [game.publisher, game.year].filter(Boolean).join(' · ')

	// The page's sections as tabs, screens first; only those the game has.
	const tabs: GameTab[] = [
		{
			id: 'screens',
			label: 'Screens',
			count: icons.length,
			panel: <IconGrid icons={icons.map(toIndexEntry)} />
		}
	]
	if (sheet && sheet.cells.length > 0)
		tabs.push({
			id: 'sprites',
			label: 'Sprites',
			count: sheet.count,
			panel: (
				<SpritesPanel
					gameSlug={game.slug}
					sheet={{
						width: sheet.width,
						height: sheet.height,
						cells: sheet.cells
					}}
				/>
			)
		})
	if (sheet && sheet.fonts.length > 0)
		tabs.push({
			id: 'fonts',
			label: 'Fonts',
			count: sheet.fonts.length,
			panel: (
				<FontsPanel
					gameSlug={game.slug}
					sheet={{
						width: sheet.width,
						height: sheet.height,
						fonts: sheet.fonts
					}}
				/>
			)
		})
	if (notes)
		tabs.push({
			id: 'notes',
			label: 'Notes',
			panel: (
				<div
					className="notes max-w-3xl"
					dangerouslySetInnerHTML={{ __html: notes }}
				/>
			)
		})

	return (
		<div className="flex flex-col gap-8">
			<header className="flex items-center justify-between gap-4">
				{/* The breadcrumb shows the title; the heading is for screen readers. */}
				<h1 className="sr-only">
					{game.name}
					{game.ja && ` (${game.ja})`}
				</h1>
				<Breadcrumb className="min-w-0">
					<BreadcrumbList className="text-xs tracking-[0.2em] uppercase">
						<BreadcrumbItem>
							<BreadcrumbLink render={<Link href="/" />}>Games</BreadcrumbLink>
						</BreadcrumbItem>
						<BreadcrumbSeparator />
						<BreadcrumbItem className="min-w-0">
							<BreadcrumbPage className="truncate" title={game.ja}>
								{game.name}
							</BreadcrumbPage>
							{meta && (
								<span className="text-muted-foreground shrink-0">· {meta}</span>
							)}
						</BreadcrumbItem>
					</BreadcrumbList>
				</Breadcrumb>
				{/*
					The game's save icons, at their own size, as its emblem: the
					first few, and a link to the rest on the save icons page.
				*/}
				{saveIcons.length > 0 && (
					<ul
						className="flex shrink-0 items-center gap-2"
						aria-label="Save icons"
					>
						{headerIcons.map(icon => (
							<li key={icon.id}>
								<Link
									href={allSaveIcons}
									title={`Save icon: ${icon.title}`}
									className="focus-visible:ring-ring block outline-none focus-visible:ring-1"
								>
									<SaveIconImage icon={toEntry(icon)} className="w-8" />
								</Link>
							</li>
						))}
						{saveIcons.length > headerIcons.length && (
							<li>
								<Link
									href={allSaveIcons}
									title={`All ${saveIcons.length} save icons`}
									className="border-border bg-card text-muted-foreground hover:border-foreground hover:bg-foreground hover:text-background focus-visible:ring-ring flex h-8 min-w-8 items-center justify-center border px-1.5 font-mono text-xs tabular-nums outline-none focus-visible:ring-1"
								>
									+{saveIcons.length - headerIcons.length}
								</Link>
							</li>
						)}
					</ul>
				)}
			</header>

			{tabs.length > 1 ? (
				<GameTabs tabs={tabs} label={`${game.name} sections`} />
			) : (
				tabs[0].panel
			)}
		</div>
	)
}
