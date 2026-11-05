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
		title: game.en,
		description: `${game.count} VMU ${game.count === 1 ? 'screen' : 'screens'} from ${game.en}${game.ja ? ` (${game.ja})` : ''}, free to download.`
	}
}

export default async function GamePage({ params }: PageProps<'/games/[slug]'>) {
	const found = getGame((await params).slug)
	if (!found) notFound()
	const { game, icons, notes } = found
	const sheet = getSpriteSheet(game.slug)
	const saveIcons = getGameSaveIcons(game.slug)
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
					{game.en}
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
								{game.en}
							</BreadcrumbPage>
							{meta && (
								<span className="text-muted-foreground shrink-0">· {meta}</span>
							)}
						</BreadcrumbItem>
					</BreadcrumbList>
				</Breadcrumb>
				{/* The game's save icons, at their own size, as its emblem. */}
				{saveIcons.length > 0 && (
					<ul className="flex shrink-0 gap-2" aria-label="Save icons">
						{saveIcons.map(icon => (
							<li key={icon.id}>
								<Link
									href={`/save-icons?${new URLSearchParams({ q: game.en })}`}
									title={`Save icon: ${icon.title}`}
									className="focus-visible:ring-ring block outline-none focus-visible:ring-1"
								>
									<SaveIconImage icon={toEntry(icon)} className="w-8" />
								</Link>
							</li>
						))}
					</ul>
				)}
			</header>

			{tabs.length > 1 ? (
				<GameTabs tabs={tabs} label={`${game.en} sections`} />
			) : (
				tabs[0].panel
			)}
		</div>
	)
}
