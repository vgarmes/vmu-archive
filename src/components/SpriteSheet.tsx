import type { CSSProperties } from 'react'
import type { SpriteSheet as Sheet } from '@/lib/sprites'

interface Props {
	gameSlug: string
	sheet: Pick<Sheet, 'width' | 'height' | 'cells' | 'count'>
}

/**
 * A game's sprites as a card under its screens: each one its own cell cut
 * from /sprites/<game slug>.png by background offset, in a wrapping row, so
 * they rewrap as the window resizes instead of the sheet scaling. Whole-number
 * scales only (1x, 2x from `sm`), since anything else drops or doubles pixel
 * rows. Closed by default: inside a closed <details> the sheet isn't fetched.
 */
export default function SpriteSheet({ gameSlug, sheet }: Props) {
	const url = `/sprites/${gameSlug}.png`
	return (
		<details className="group border-border bg-card/50 border">
			<summary className="hover:text-foreground text-muted-foreground focus-visible:ring-ring flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3 text-xs tracking-[0.2em] uppercase outline-none focus-visible:ring-1 [&::-webkit-details-marker]:hidden">
				<span>
					Sprites{' '}
					<span className="text-muted-foreground/70">({sheet.count})</span>
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
					Smaller art the game draws onto part of a screen, kept for
					preservation. Hover one for its name.
				</p>
				{/*
					The sheet and scale are set once here; each cell only has its box.
					A strip wider than the column at 2x (the VMU's 336x8 font, just
					above `sm`) scrolls inside the card, like a wide table.
				*/}
				<ul
					className="flex flex-wrap items-end gap-1 overflow-x-auto [--s:1] sm:[--s:2]"
					style={
						{
							'--sheet': `url(${url})`,
							'--sheet-w': `${sheet.width}px`,
							'--sheet-h': `${sheet.height}px`
						} as CSSProperties
					}
				>
					{sheet.cells.map((c, i) => (
						<li
							key={i}
							title={c.title}
							className="bg-muted h-[calc(var(--h)*var(--s))] w-[calc(var(--w)*var(--s))] shrink-0"
							style={
								{
									'--w': `${c.width}px`,
									'--h': `${c.height}px`,
									'--x': `${-c.x}px`,
									'--y': `${-c.y}px`
								} as CSSProperties
							}
						>
							<span
								aria-hidden="true"
								className="pixelated block size-full bg-(image:--sheet) bg-[size:calc(var(--sheet-w)*var(--s))_calc(var(--sheet-h)*var(--s))] bg-[position:calc(var(--x)*var(--s))_calc(var(--y)*var(--s))] dark:invert"
							/>
							<span className="sr-only">{c.title}</span>
						</li>
					))}
				</ul>
			</div>
		</details>
	)
}
