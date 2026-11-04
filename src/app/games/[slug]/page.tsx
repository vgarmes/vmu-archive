import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import IconGrid from '@/components/IconGrid'
import SpriteSheet from '@/components/SpriteSheet'
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
	const meta = [game.publisher, game.year].filter(Boolean).join(' · ')

	return (
		<div className="flex flex-col gap-8">
			<header>
				{/* The breadcrumb shows the title; the heading is for screen readers. */}
				<h1 className="sr-only">
					{game.en}
					{game.ja && ` (${game.ja})`}
				</h1>
				<Breadcrumb>
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
			</header>

			<IconGrid icons={icons.map(toIndexEntry)} />

			{sheet && (
				<SpriteSheet
					gameSlug={game.slug}
					sheet={{
						width: sheet.width,
						height: sheet.height,
						cells: sheet.cells,
						count: sheet.count
					}}
				/>
			)}

			{notes && (
				<details className="group border-border bg-card/50 border">
					<summary className="hover:text-foreground text-muted-foreground focus-visible:ring-ring flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3 text-xs tracking-[0.2em] uppercase outline-none focus-visible:ring-1 [&::-webkit-details-marker]:hidden">
						How these screens were extracted
						<span
							aria-hidden="true"
							className="transition-transform group-open:rotate-45"
						>
							+
						</span>
					</summary>
					<div
						className="notes border-border max-w-3xl border-t px-4 py-4"
						dangerouslySetInnerHTML={{ __html: notes }}
					/>
				</details>
			)}
		</div>
	)
}
