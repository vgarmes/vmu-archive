'use client'

import { useEffect, useMemo, useState } from 'react'
import { ColorsPicker, lcdColors, useColors } from '@/components/ColorPresets'
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue
} from '@/components/ui/Select'
import { encodeFrame, toSvg } from '@/lib/pixels'
import {
	ANIMALS,
	CYCLE_STEPS,
	describeClock,
	HEIGHT,
	makeClockDrawer,
	WIDTH,
	type Animal,
	type ClockArt
} from '@/lib/vmu-clock'

type View = 'time' | 'date'

const VIEWS: { value: View; label: string }[] = [
	{ value: 'time', label: 'Time' },
	{ value: 'date', label: 'Date' }
]
const ANIMAL_ITEMS = ANIMALS.map(a => ({
	value: a,
	label: a[0].toUpperCase() + a.slice(1)
}))

/** Whether the visitor asks for reduced motion. */
function useReducedMotion() {
	const [reduced, setReduced] = useState(false)
	useEffect(() => {
		const media = matchMedia('(prefers-reduced-motion: reduce)')
		const update = () => setReduced(media.matches)
		update()
		media.addEventListener('change', update)
		return () => media.removeEventListener('change', update)
	}, [])
	return reduced
}

/**
 * The visitor's clock, ticking on the second like the VMU's. `steps` counts
 * the seconds since the screen was last drawn, which is what moves the
 * animal; it starts over whenever the view or the animal changes, as the BIOS
 * redraws the screen then. Nothing is shown until mounted, so the server's
 * render (which has no visitor time) matches the first one in the browser.
 */
function useClock(view: View, animal: Animal) {
	const [now, setNow] = useState<Date | null>(null)
	const [steps, setSteps] = useState(0)

	useEffect(() => setSteps(0), [view, animal])

	useEffect(() => {
		let timer: ReturnType<typeof setTimeout>
		const tick = (first: boolean) => {
			setNow(new Date())
			if (!first) setSteps(s => s + 1)
			// Wake just after the next second starts, not every 1000 ms from
			// whenever the page loaded.
			timer = setTimeout(() => tick(false), 1000 - (Date.now() % 1000) + 5)
		}
		tick(true)
		return () => clearTimeout(timer)
	}, [])

	return { now, steps }
}

export default function VmuClock({ art }: { art: ClockArt }) {
	const [view, setView] = useState<View>('time')
	const [animal, setAnimal] = useState<Animal>('dog')
	const colors = useColors()
	const reduced = useReducedMotion()
	const { now, steps } = useClock(view, animal)
	const draw = useMemo(() => makeClockDrawer(art), [art])

	// With reduced motion the animal holds still, its whole trail drawn.
	const shown = reduced ? CYCLE_STEPS / 2 : steps
	const screen = now
		? draw({ view, now, animal, steps: shown })
		: new Uint8Array(WIDTH * HEIGHT)
	const label = now
		? describeClock({ view, now, animal, steps: shown })
		: 'VMU clock'
	const svg = toSvg(
		{ width: WIDTH, height: HEIGHT, bpp: 1, frames: [encodeFrame(screen, 1)] },
		{
			style: 'lcd',
			...lcdColors(colors).preview,
			attrs: `class="block h-auto w-full" role="img" aria-label="${label}"`
		}
	)

	return (
		// One centred column, no wider than max-w-md at any screen size.
		<div className="mx-auto flex w-full max-w-md flex-col gap-8">
			{/* min-w-0 so the SVG's 384px size doesn't stop it shrinking. */}
			<div
				className="aspect-[3/2] w-full min-w-0"
				dangerouslySetInnerHTML={{ __html: svg }}
			/>

			<div className="grid grid-cols-[auto_1fr] items-center gap-x-4 gap-y-3 text-sm">
				<span className="text-muted-foreground">Screen</span>
				<Select items={VIEWS} value={view} onValueChange={v => v && setView(v)}>
					<SelectTrigger aria-label="Screen" className="w-full">
						<SelectValue />
					</SelectTrigger>
					<SelectContent alignItemWithTrigger={false}>
						{VIEWS.map(v => (
							<SelectItem key={v.value} value={v.value}>
								{v.label}
							</SelectItem>
						))}
					</SelectContent>
				</Select>

				<span className="text-muted-foreground">Animal</span>
				<Select
					items={ANIMAL_ITEMS}
					value={animal}
					onValueChange={v => {
						if (!v) return
						setAnimal(v)
						// Picking one goes back to the time, as the BIOS's menu does.
						setView('time')
					}}
				>
					<SelectTrigger aria-label="Animal" className="w-full">
						<SelectValue />
					</SelectTrigger>
					<SelectContent alignItemWithTrigger={false}>
						{ANIMAL_ITEMS.map(a => (
							<SelectItem key={a.value} value={a.value}>
								{a.label}
							</SelectItem>
						))}
					</SelectContent>
				</Select>

				<span className="text-muted-foreground">Colors</span>
				<ColorsPicker colors={colors} />
			</div>
		</div>
	)
}
