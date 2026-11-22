'use client'

import { useEffect, useState } from 'react'

/** Whether the visitor asks for reduced motion. */
export function useReducedMotion() {
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
 * animal; it starts over whenever `redraw` changes, as the BIOS redraws the
 * screen when the view or the animal changes. `now` is null until mounted,
 * so the server's render (which has no visitor time) matches the first one
 * in the browser.
 */
export function useClock(redraw = '') {
	const [now, setNow] = useState<Date | null>(null)
	const [steps, setSteps] = useState(0)

	useEffect(() => setSteps(0), [redraw])

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
