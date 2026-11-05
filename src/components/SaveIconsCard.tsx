import Link from 'next/link'
import SaveIconImage from '@/components/SaveIconImage'
import type { SaveIconEntry } from '@/lib/save-icons'

/**
 * A game's save icons as a card under its screens, like the Sprites and Fonts
 * cards: each icon at 2x with its title, and a link to the /save-icons page
 * searched for the game.
 */
export default function SaveIconsCard({
	icons,
	game
}: {
	icons: SaveIconEntry[]
	game: string
}) {
	return (
		<details className="group border-border bg-card/50 border">
			<summary className="hover:text-foreground text-muted-foreground focus-visible:ring-ring flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3 text-xs tracking-[0.2em] uppercase outline-none focus-visible:ring-1 [&::-webkit-details-marker]:hidden">
				<span>
					Save icons{' '}
					<span className="text-muted-foreground/70">({icons.length})</span>
				</span>
				<span
					aria-hidden="true"
					className="transition-transform group-open:rotate-45"
				>
					+
				</span>
			</summary>
			<div className="border-border flex flex-col gap-3 border-t px-4 py-4">
				<p className="text-muted-foreground max-w-3xl text-xs">
					The icons the Dreamcast&apos;s memory card menu shows for this
					game&apos;s saves.{' '}
					<Link
						href={`/save-icons?${new URLSearchParams({ q: game })}`}
						className="hover:text-foreground underline underline-offset-2"
					>
						All save icons
					</Link>
				</p>
				<ul className="flex flex-wrap gap-4">
					{icons.map(icon => (
						<li key={icon.id} className="flex flex-col items-center gap-1.5">
							<SaveIconImage icon={icon} className="w-16" />
							<span className="text-muted-foreground text-xs">
								{icon.title}
							</span>
						</li>
					))}
				</ul>
			</div>
		</details>
	)
}
