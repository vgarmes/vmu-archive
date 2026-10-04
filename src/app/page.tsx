import Archive from '@/components/Archive'
import { getIcons, toIndexEntry } from '@/lib/icons'

export default function Home() {
	const icons = getIcons()
	// The first batch is rendered into the HTML; the grid fetches the rest.
	const initial = icons.slice(0, 60).map(toIndexEntry)
	return (
		<>
			<section className="mb-8 flex flex-col gap-2">
				{/* Hidden visually; kept so the page still has a main heading. */}
				<h1 className="sr-only">Dreamcast VMU pixel art</h1>
				<p className="text-muted-foreground max-w-2xl text-sm">
					Screen art from the Dreamcast&apos;s Visual Memory Unit. Search the
					archive and download any piece as PNG, SVG, GIF or C source.
				</p>
			</section>
			<Archive initial={initial} total={icons.length} />
		</>
	)
}
