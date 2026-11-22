'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { useClock, useReducedMotion } from '@/components/useClock'
import { encodeFrame, toSvg } from '@/lib/pixels'
import {
	CYCLE_STEPS,
	makeClockStripDrawer,
	STRIP_HEIGHT,
	STRIP_WIDTH,
	type ClockArt
} from '@/lib/vmu-clock'

/**
 * The visitor's time in the VMU clock's big font, with its bird taking off
 * beside it once a second, drawn in the text colour. Links to the clock.
 */
export default function FooterClock({ art }: { art: ClockArt }) {
	const draw = useMemo(() => makeClockStripDrawer(art), [art])
	const reduced = useReducedMotion()
	const { now, steps } = useClock()

	// With reduced motion the bird holds still, its whole trail drawn.
	const dots = now
		? draw({ now, steps: reduced ? CYCLE_STEPS / 2 : steps })
		: new Uint8Array(STRIP_WIDTH * STRIP_HEIGHT)
	const time = now
		? `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
		: ''
	const svg = toSvg(
		{
			width: STRIP_WIDTH,
			height: STRIP_HEIGHT,
			bpp: 1,
			frames: [encodeFrame(dots, 1)]
		},
		// 2px a dot; aria-hidden, as the link says the time.
		{ on: 'currentColor', attrs: 'class="block h-7 w-auto" aria-hidden="true"' }
	)

	return (
		<Link
			href="/clock"
			aria-label={time ? `Clock, ${time}` : 'Clock'}
			className="text-muted-foreground hover:text-foreground focus-visible:ring-ring block transition-colors outline-none focus-visible:ring-1"
		>
			<span className="block" dangerouslySetInnerHTML={{ __html: svg }} />
		</Link>
	)
}
