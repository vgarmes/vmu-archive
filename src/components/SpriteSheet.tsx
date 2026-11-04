import type { CSSProperties, ReactNode } from 'react'
import type { SpriteCell, SpriteSheet as Sheet } from '@/lib/sprites'
import { cn } from 'cn'

type SheetProps = Pick<Sheet, 'width' | 'height'>

/**
 * A game's sprites and fonts as cards under its screens: each piece its own
 * cell cut from /sprites/<game slug>.png by background offset, in wrapping
 * rows, so they rewrap as the window resizes instead of the sheet scaling.
 * Whole-number scales only, since anything else drops or doubles pixel rows.
 * Closed by default: inside a closed <details> the sheet isn't fetched.
 */
function Card({
	label,
	count,
	blurb,
	gameSlug,
	sheet,
	children
}: {
	label: string
	count: number
	blurb: string
	gameSlug: string
	sheet: SheetProps
	children: ReactNode
}) {
	return (
		<details className="group border-border bg-card/50 border">
			<summary className="hover:text-foreground text-muted-foreground focus-visible:ring-ring flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3 text-xs tracking-[0.2em] uppercase outline-none focus-visible:ring-1 [&::-webkit-details-marker]:hidden">
				<span>
					{label} <span className="text-muted-foreground/70">({count})</span>
				</span>
				<span
					aria-hidden="true"
					className="transition-transform group-open:rotate-45"
				>
					+
				</span>
			</summary>
			{/* The sheet is set once here; each cell only has its box. */}
			<div
				className="border-border flex flex-col gap-3 border-t px-4 py-4"
				style={
					{
						'--sheet': `url(/sprites/${gameSlug}.png)`,
						'--sheet-w': `${sheet.width}px`,
						'--sheet-h': `${sheet.height}px`
					} as CSSProperties
				}
			>
				<p className="text-muted-foreground max-w-3xl text-xs">{blurb}</p>
				{children}
			</div>
		</details>
	)
}

/**
 * Cells at the scale `--s` the class sets. A strip wider than the column
 * scrolls inside the card, like a wide table. `boxed` shades each cell's box,
 * so a sprite's size shows; characters go without, on the page's background.
 */
function Cells({
	cells,
	className,
	boxed = true
}: {
	cells: SpriteCell[]
	className: string
	boxed?: boolean
}) {
	return (
		<ul className={cn('flex flex-wrap items-end overflow-x-auto', className)}>
			{cells.map((c, i) => (
				<li
					key={i}
					title={c.title}
					className={cn(
						'h-[calc(var(--h)*var(--s))] w-[calc(var(--w)*var(--s))] shrink-0',
						boxed && 'bg-muted'
					)}
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
	)
}

/** The sprites that aren't fonts, one cell each, at 1x (2x from `sm`). */
export default function SpriteSheet({
	gameSlug,
	sheet
}: {
	gameSlug: string
	sheet: SheetProps & Pick<Sheet, 'cells' | 'count'>
}) {
	return (
		<Card
			label="Sprites"
			count={sheet.count}
			blurb="Smaller art the game draws onto part of a screen, kept for preservation. Hover one for its name."
			gameSlug={gameSlug}
			sheet={sheet}
		>
			<Cells cells={sheet.cells} className="gap-1 [--s:1] sm:[--s:2]" />
		</Card>
	)
}

/**
 * The fonts, each under its name: its characters in the game's order, a small
 * gap apart and on the page's background, at 2x (3x from `sm`).
 */
export function FontSheet({
	gameSlug,
	sheet
}: {
	gameSlug: string
	sheet: SheetProps & Pick<Sheet, 'fonts'>
}) {
	return (
		<Card
			label="Fonts"
			count={sheet.fonts.length}
			blurb="The game's fonts, each character in the order the game stores them. Blank characters are left out. Hover one for its number."
			gameSlug={gameSlug}
			sheet={sheet}
		>
			{sheet.fonts.map(f => (
				<section key={f.title} className="flex flex-col gap-1.5">
					<h3 className="text-muted-foreground text-xs">
						{f.title}
						{f.split && (
							<span className="text-muted-foreground/70">
								{' '}
								· {f.cells.length} characters
							</span>
						)}
					</h3>
					<Cells
						cells={f.cells}
						boxed={false}
						className="gap-1 [--s:2] sm:[--s:3]"
					/>
				</section>
			))}
		</Card>
	)
}
