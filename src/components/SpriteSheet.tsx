import type { CSSProperties, ReactNode } from 'react'
import type { SpriteCell, SpriteSheet as Sheet } from '@/lib/sprites'
import { cn } from 'cn'

type SheetProps = Pick<Sheet, 'width' | 'height'>

/**
 * A game's sprites and fonts, each the content of a tab on its page: each
 * piece its own cell cut from /sprites/<game slug>.png by background offset,
 * in wrapping rows, so they rewrap as the window resizes instead of the sheet
 * scaling. Whole-number scales only, since anything else drops or doubles
 * pixel rows. In a hidden tab the sheet isn't fetched.
 */
function Panel({
	blurb,
	gameSlug,
	sheet,
	children
}: {
	blurb: string
	gameSlug: string
	sheet: SheetProps
	children: ReactNode
}) {
	return (
		// The sheet is set once here; each cell only has its box.
		<div
			className="flex flex-col gap-4"
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

/**
 * The sprites that aren't fonts, one cell each, at the fonts' scale, 2x (3x
 * from `sm`), so a VMU dot is the same size in both tabs.
 */
export default function SpritesPanel({
	gameSlug,
	sheet
}: {
	gameSlug: string
	sheet: SheetProps & Pick<Sheet, 'cells'>
}) {
	return (
		<Panel
			blurb="Smaller art the game draws onto part of a screen, kept for preservation. Hover one for its name."
			gameSlug={gameSlug}
			sheet={sheet}
		>
			<Cells cells={sheet.cells} className="gap-1 [--s:2] sm:[--s:3]" />
		</Panel>
	)
}

/**
 * The fonts, each under its name: its characters in the game's order, a small
 * gap apart and on the page's background, at 2x (3x from `sm`).
 */
export function FontsPanel({
	gameSlug,
	sheet
}: {
	gameSlug: string
	sheet: SheetProps & Pick<Sheet, 'fonts'>
}) {
	return (
		<Panel
			blurb="The game's fonts, each character in the order the game stores them. Blank characters are left out. Hover one for its number."
			gameSlug={gameSlug}
			sheet={sheet}
		>
			{sheet.fonts.map(f => (
				<section key={f.title} className="flex flex-col gap-1.5">
					<h3 className="text-muted-foreground text-xs">
						{f.title}
						{f.split && (
							<span className="text-muted-foreground/70 font-mono">
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
		</Panel>
	)
}
