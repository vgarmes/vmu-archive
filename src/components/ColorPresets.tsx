'use client'

import { ArrowLeftRightIcon } from 'lucide-react'
import { useEffect, useState } from 'react'
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue
} from '@/components/ui/Select'
import { LCD_INK, parseColor, toHexColor } from '@/lib/pixels'

/**
 * Colour presets: the ink of lit pixels, used by every export, and the screen
 * behind them, used by the preview and the LCD-dots SVG only (the other
 * formats stay transparent). Those two draw unlit dots too, in `off`, with the
 * screen showing in the gaps between dots; without an `off` they're the ink
 * at ~12%. "Site theme" has none: the preview follows the page and exports use
 * the default ink, as before presets.
 *
 * Shared by the sprite drawer and the clock page, and saved once per browser,
 * so a preset picked in one is the one the other shows.
 */
export const PALETTES = [
	{ id: 'site', name: 'Site theme', ink: null, off: null, screen: null },
	// VMU and LCD are the DreamPotato emulator's Dark Green and VM2 palettes,
	// all three tones: Screen1 (lit) as ink, Screen0 (unlit) as off and its
	// lighter Margin, the frame round the screen, as the screen in the gaps.
	{
		id: 'vmu',
		name: 'VMU',
		ink: '#231024',
		off: '#3e4e44',
		screen: '#4d594b'
	},
	{
		id: 'lcd',
		name: 'LCD',
		ink: '#000000',
		off: '#9fcede',
		screen: '#b5d3dd'
	},
	{ id: 'mono', name: 'Mono', ink: '#000000', off: null, screen: '#ffffff' },
	{
		id: 'gameboy',
		name: 'Game Boy',
		ink: '#0f380f',
		off: null,
		screen: '#9bbc0f'
	}
] as const
type PaletteId = (typeof PALETTES)[number]['id']
const COLORS_KEY = 'vmu-archive:colors'

/** The chosen preset and whether its colours are swapped, kept per browser. */
export function useColors() {
	const [colors, setColors] = useState<{ id: PaletteId; swapped: boolean }>({
		id: 'site',
		swapped: false
	})
	useEffect(() => {
		try {
			const saved = JSON.parse(localStorage.getItem(COLORS_KEY) ?? 'null')
			if (saved && PALETTES.some(p => p.id === saved.id))
				setColors({ id: saved.id, swapped: !!saved.swapped })
		} catch {}
	}, [])
	const update = (next: { id: PaletteId; swapped: boolean }) => {
		setColors(next)
		try {
			localStorage.setItem(COLORS_KEY, JSON.stringify(next))
		} catch {}
	}
	const palette = PALETTES.find(p => p.id === colors.id) ?? PALETTES[0]
	if (!colors.swapped)
		return {
			...colors,
			palette,
			ink: palette.ink,
			off: palette.off,
			screen: palette.screen,
			update
		}
	// Swapping trades lit for unlit: the ink takes the unlit colour (or the
	// screen, for a preset without one) and the unlit dots and the gaps
	// between them take the ink. The lighter frame colour isn't kept in the
	// gaps, where it would draw a bright grid round the now-dark dots.
	return {
		...colors,
		palette,
		ink: palette.off ?? palette.screen,
		off: palette.off ? palette.ink : null,
		screen: palette.ink,
		update
	}
}

export type Colors = ReturnType<typeof useColors>

/**
 * What the LCD-dot style draws with for the chosen colours: the ink as RGBA
 * (for PNG and GIF) and hex, the unlit dots and the preview's SVG options.
 * Unlit dots are the preset's own unlit colour, or else the ink at ~12%
 * opacity; toHexColor already includes the alpha, so that colour is built
 * rather than appended to. "Site theme" follows the page's text colour.
 */
export function lcdColors(colors: Colors) {
	const inkRgba = colors.ink ? parseColor(colors.ink) : LCD_INK
	const ink = toHexColor(inkRgba)
	const [r, g, b] = inkRgba
	const unlit = colors.off ?? toHexColor([r, g, b, 0x1f])
	const preview = colors.ink
		? { on: ink, off: unlit, background: colors.screen ?? undefined }
		: {
				on: 'currentColor',
				off: 'color-mix(in srgb, currentColor 10%, transparent)'
			}
	return { inkRgba, ink, unlit, preview }
}

/** A preset's colours: an ink square on its unlit colour, or its screen. */
function Swatch({
	ink,
	screen
}: {
	ink: string | null
	screen: string | null
}) {
	return (
		<span
			aria-hidden="true"
			className="border-border inline-flex size-4 shrink-0 border"
			style={{ background: screen ?? 'transparent' }}
		>
			<span
				className="m-auto size-2"
				style={{ background: ink ?? 'currentColor' }}
			/>
		</span>
	)
}

/** The preset picker and the button that swaps ink and screen. */
export function ColorsPicker({ colors }: { colors: Colors }) {
	return (
		<div className="flex min-w-0 gap-2">
			<Select
				items={PALETTES.map(p => ({ value: p.id, label: p.name }))}
				value={colors.id}
				onValueChange={v => v && colors.update({ id: v, swapped: false })}
			>
				<SelectTrigger aria-label="Colors" className="min-w-0 flex-1">
					<SelectValue>
						{() => (
							<span className="flex items-center gap-2">
								<Swatch ink={colors.ink} screen={colors.off ?? colors.screen} />
								{colors.palette.name}
							</span>
						)}
					</SelectValue>
				</SelectTrigger>
				<SelectContent alignItemWithTrigger={false}>
					{PALETTES.map(p => (
						<SelectItem key={p.id} value={p.id}>
							<span className="flex items-center gap-2">
								<Swatch ink={p.ink} screen={p.off ?? p.screen} />
								{p.name}
							</span>
						</SelectItem>
					))}
				</SelectContent>
			</Select>
			<button
				type="button"
				onClick={() =>
					colors.update({ id: colors.id, swapped: !colors.swapped })
				}
				disabled={!colors.palette.ink}
				aria-pressed={colors.swapped}
				aria-label="Swap ink and screen colors"
				title="Swap ink and screen colors"
				className="border-input enabled:hover:border-foreground text-muted-foreground enabled:hover:text-foreground aria-pressed:text-foreground flex size-8 shrink-0 items-center justify-center rounded-lg border disabled:opacity-40"
			>
				<ArrowLeftRightIcon className="size-4" aria-hidden="true" />
			</button>
		</div>
	)
}
