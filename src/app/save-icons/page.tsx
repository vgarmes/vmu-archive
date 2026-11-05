import type { Metadata } from 'next'
import SaveIconIndex from '@/components/SaveIconIndex'
import { getSaveIcons, toEntry } from '@/lib/save-icons'

export const metadata: Metadata = {
	title: 'Save icons',
	description:
		'The colour icons the Dreamcast shows for each game save, from every game in one place.'
}

export default function SaveIcons() {
	return (
		<>
			<section className="mb-8 flex flex-col gap-2">
				<h1 className="text-sm font-normal tracking-[0.2em] uppercase">
					Save icons
				</h1>
				<p className="text-muted-foreground max-w-2xl text-sm">
					The icons the Dreamcast&apos;s memory card menu shows for each save,
					read from the saves themselves: 32×32, in 16 colours. Saves that carry
					the same icon are shown once.
				</p>
			</section>
			<SaveIconIndex icons={getSaveIcons().map(toEntry)} />
		</>
	)
}
