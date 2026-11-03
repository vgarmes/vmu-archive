import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import IconGrid from '@/components/IconGrid'
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
	const meta = [game.publisher, game.year].filter(Boolean).join(' · ')

	return (
		<div className="flex flex-col gap-8">
			<header className="flex flex-col gap-3">
				<Breadcrumb>
					<BreadcrumbList className="text-xs tracking-[0.2em] uppercase">
						<BreadcrumbItem>
							<BreadcrumbLink render={<Link href="/" />}>Games</BreadcrumbLink>
						</BreadcrumbItem>
						<BreadcrumbSeparator />
						<BreadcrumbItem className="min-w-0">
							<BreadcrumbPage className="truncate">{game.en}</BreadcrumbPage>
						</BreadcrumbItem>
					</BreadcrumbList>
				</Breadcrumb>
				<div className="flex flex-col gap-1">
					<h1 className="text-base font-bold">{game.en}</h1>
					{game.ja && (
						<p className="text-muted-foreground text-sm">{game.ja}</p>
					)}
					{meta && <p className="text-muted-foreground text-xs">{meta}</p>}
				</div>
			</header>

			<IconGrid icons={icons.map(toIndexEntry)} />

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
