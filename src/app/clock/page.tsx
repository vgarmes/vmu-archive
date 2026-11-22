import type { Metadata } from 'next'
import Link from 'next/link'
import VmuClock from '@/components/VmuClock'
import { getClockArt } from '@/lib/vmu-clock-art'

export const metadata: Metadata = {
	title: 'Clock',
	description:
		"The VMU's clock screen, redrawn from its BIOS: the time with a dog, fish or bird walking below, or the date."
}

export default function ClockPage() {
	return (
		<>
			<section className="mb-8 flex flex-col gap-2">
				<h1 className="text-sm font-normal tracking-[0.2em] uppercase">
					Clock
				</h1>
				<p className="text-muted-foreground max-w-2xl text-sm">
					Your time on the{' '}
					<Link
						href="/games/visual-memory-unit"
						className="hover:text-foreground underline underline-offset-4"
					>
						Visual Memory Unit
					</Link>
					&apos;s clock screen, drawn as its BIOS draws it, from the
					archive&apos;s font and animals: the time with an animal walking below
					it, or the date.
				</p>
			</section>
			<VmuClock art={getClockArt()} />
		</>
	)
}
